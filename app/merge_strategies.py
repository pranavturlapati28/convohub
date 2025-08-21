from typing import Dict, List, Optional, Any, Protocol, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from sqlalchemy.orm import Session
from datetime import datetime
import json
import re

from app.models import Thread, Branch, Summary, Memory, Merge
from app.llm import assistant_reply


@dataclass
class MergeContext:
    """Context for merge operations"""
    thread_id: str
    source_branch_id: str
    target_branch_id: str
    merge_id: str
    db: Session


@dataclass
class MergedSummary:
    """Result of summary merging"""
    content: str
    metadata: Dict[str, Any]
    version: str = "1.0"


@dataclass
class MergedMemory:
    """Result of memory merging"""
    key: str
    value: str
    memory_type: str
    confidence: str
    source: str
    metadata: Dict[str, Any]


@dataclass
class MergeResult:
    """Complete result of merge strategy"""
    summary: Optional[MergedSummary]
    memories: List[MergedMemory]
    metadata: Dict[str, Any]


class MergeStrategy(ABC):
    """Abstract base class for merge strategies"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def merge_summaries_and_memories(
        self, 
        context: MergeContext
    ) -> MergeResult:
        """
        Merge summaries and memories from source and target branches.
        
        Args:
            context: Merge context with branch and thread information
            
        Returns:
            MergeResult: Merged summary and memories
        """
        pass
    
    def _get_branch_summaries(self, branch_id: str) -> List[Summary]:
        """Get all summaries for a branch's thread."""
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            return []
        
        return (self.db.query(Summary)
                .filter(
                    Summary.thread_id == branch.thread_id,
                    Summary.is_current == True
                )
                .all())
    
    def _get_branch_memories(self, branch_id: str) -> List[Memory]:
        """Get all memories for a branch's thread."""
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            return []
        
        return (self.db.query(Memory)
                .filter(Memory.thread_id == branch.thread_id)
                .all())


class AppendLastStrategy(MergeStrategy):
    """
    Baseline merge strategy: append-last approach.
    
    - Summary: Concatenate parent summaries
    - Memory: Union with newest-wins conflict resolution
    """
    
    def merge_summaries_and_memories(
        self, 
        context: MergeContext
    ) -> MergeResult:
        """Implement append-last merge strategy."""
        
        # Get summaries from both branches
        source_summaries = self._get_branch_summaries(context.source_branch_id)
        target_summaries = self._get_branch_summaries(context.target_branch_id)
        
        # Get memories from both branches
        source_memories = self._get_branch_memories(context.source_branch_id)
        target_memories = self._get_branch_memories(context.target_branch_id)
        
        # Merge summaries: concatenate with separator
        merged_summary = self._merge_summaries_append_last(source_summaries, target_summaries)
        
        # Merge memories: union with newest-wins
        merged_memories = self._merge_memories_union_newest_wins(source_memories, target_memories)
        
        return MergeResult(
            summary=merged_summary,
            memories=merged_memories,
            metadata={
                "strategy": "append-last",
                "source_summaries": len(source_summaries),
                "target_summaries": len(target_summaries),
                "source_memories": len(source_memories),
                "target_memories": len(target_memories),
                "merged_at": datetime.utcnow().isoformat()
            }
        )
    
    def _merge_summaries_append_last(
        self, 
        source_summaries: List[Summary], 
        target_summaries: List[Summary]
    ) -> Optional[MergedSummary]:
        """Concatenate summaries with separator."""
        
        summary_parts = []
        
        # Add target summaries first (they're the "base")
        for summary in target_summaries:
            if summary.content:
                summary_parts.append(f"[Target Branch Summary]\n{summary.content}")
        
        # Add source summaries
        for summary in source_summaries:
            if summary.content:
                summary_parts.append(f"[Source Branch Summary]\n{summary.content}")
        
        if not summary_parts:
            return None
        
        # Concatenate with separator
        merged_content = "\n\n---\n\n".join(summary_parts)
        
        return MergedSummary(
            content=merged_content,
            metadata={
                "merge_strategy": "append-last",
                "source_summary_count": len(source_summaries),
                "target_summary_count": len(target_summaries),
                "merged_at": datetime.utcnow().isoformat()
            }
        )
    
    def _merge_memories_union_newest_wins(
        self, 
        source_memories: List[Memory], 
        target_memories: List[Memory]
    ) -> List[MergedMemory]:
        """Union memories with newest-wins conflict resolution."""
        
        # Create a map of key -> memory for conflict resolution
        memory_map = {}
        
        # Add target memories first
        for memory in target_memories:
            memory_map[memory.key] = {
                "memory": memory,
                "timestamp": memory.created_at,
                "source": "target"
            }
        
        # Add source memories, overwriting if newer
        for memory in source_memories:
            existing = memory_map.get(memory.key)
            if not existing or memory.created_at > existing["timestamp"]:
                memory_map[memory.key] = {
                    "memory": memory,
                    "timestamp": memory.created_at,
                    "source": "source"
                }
        
        # Convert to MergedMemory objects
        merged_memories = []
        for key, info in memory_map.items():
            memory = info["memory"]
            merged_memories.append(MergedMemory(
                key=memory.key,
                value=memory.value,
                memory_type=memory.memory_type,
                confidence=memory.confidence,
                source=f"merge_{info['source']}",
                metadata={
                    "original_source": info["source"],
                    "original_id": memory.id,
                    "merge_strategy": "append-last",
                    "merged_at": datetime.utcnow().isoformat()
                }
            ))
        
        return merged_memories


class ResolverStrategy(MergeStrategy):
    """
    LLM-based merge strategy: uses deterministic prompt & JSON schema.
    
    - Summary: LLM generates coherent merged summary
    - Memory: LLM resolves conflicts and deduplicates
    """
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.summary_prompt = self._get_summary_merge_prompt()
        self.memory_prompt = self._get_memory_merge_prompt()
    
    def merge_summaries_and_memories(
        self, 
        context: MergeContext
    ) -> MergeResult:
        """Implement LLM resolver merge strategy."""
        
        # Get summaries and memories from both branches
        source_summaries = self._get_branch_summaries(context.source_branch_id)
        target_summaries = self._get_branch_summaries(context.target_branch_id)
        source_memories = self._get_branch_memories(context.source_branch_id)
        target_memories = self._get_branch_memories(context.target_branch_id)
        
        # Merge summaries using LLM
        merged_summary = self._merge_summaries_with_llm(source_summaries, target_summaries)
        
        # Merge memories using LLM
        merged_memories = self._merge_memories_with_llm(source_memories, target_memories)
        
        return MergeResult(
            summary=merged_summary,
            memories=merged_memories,
            metadata={
                "strategy": "resolver",
                "source_summaries": len(source_summaries),
                "target_summaries": len(target_summaries),
                "source_memories": len(source_memories),
                "target_memories": len(target_memories),
                "merged_at": datetime.utcnow().isoformat()
            }
        )
    
    def _merge_summaries_with_llm(
        self, 
        source_summaries: List[Summary], 
        target_summaries: List[Summary]
    ) -> Optional[MergedSummary]:
        """Use LLM to merge summaries coherently."""
        
        if not source_summaries and not target_summaries:
            return None
        
        # Prepare input for LLM
        source_content = "\n\n".join([s.content for s in source_summaries if s.content])
        target_content = "\n\n".join([s.content for s in target_summaries if s.content])
        
        # Create LLM input
        llm_input = f"""
{self.summary_prompt}

TARGET BRANCH SUMMARIES:
{target_content}

SOURCE BRANCH SUMMARIES:
{source_content}

Please merge these summaries into a coherent, unified summary.
"""
        
        # Get LLM response
        try:
            llm_response = assistant_reply([{"role": "user", "content": llm_input}])
            
            # Try to parse JSON response
            try:
                parsed = json.loads(llm_response)
                if isinstance(parsed, dict) and "summary" in parsed:
                    return MergedSummary(
                        content=parsed["summary"],
                        metadata={
                            "merge_strategy": "resolver",
                            "llm_response": llm_response,
                            "source_summary_count": len(source_summaries),
                            "target_summary_count": len(target_summaries),
                            "merged_at": datetime.utcnow().isoformat()
                        }
                    )
            except json.JSONDecodeError:
                pass
            
            # Fallback: use raw response as summary
            return MergedSummary(
                content=llm_response,
                metadata={
                    "merge_strategy": "resolver",
                    "llm_response": llm_response,
                    "fallback": True,
                    "source_summary_count": len(source_summaries),
                    "target_summary_count": len(target_summaries),
                    "merged_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            # Fallback to append-last if LLM fails
            fallback_strategy = AppendLastStrategy(self.db)
            return fallback_strategy._merge_summaries_append_last(source_summaries, target_summaries)
    
    def _merge_memories_with_llm(
        self, 
        source_memories: List[Memory], 
        target_memories: List[Memory]
    ) -> List[MergedMemory]:
        """Use LLM to merge memories intelligently."""
        
        if not source_memories and not target_memories:
            return []
        
        # Prepare memory data for LLM
        source_memory_data = [
            {
                "key": m.key,
                "value": m.value,
                "type": m.memory_type,
                "confidence": m.confidence,
                "source": "source"
            }
            for m in source_memories
        ]
        
        target_memory_data = [
            {
                "key": m.key,
                "value": m.value,
                "type": m.memory_type,
                "confidence": m.confidence,
                "source": "target"
            }
            for m in target_memories
        ]
        
        # Create LLM input
        llm_input = f"""
{self.memory_prompt}

TARGET BRANCH MEMORIES:
{json.dumps(target_memory_data, indent=2)}

SOURCE BRANCH MEMORIES:
{json.dumps(source_memory_data, indent=2)}

Please merge these memories, resolving conflicts and deduplicating where appropriate.
"""
        
        # Get LLM response
        try:
            llm_response = assistant_reply([{"role": "user", "content": llm_input}])
            
            # Try to parse JSON response
            try:
                parsed = json.loads(llm_response)
                if isinstance(parsed, dict) and "memories" in parsed:
                    memories = []
                    for mem_data in parsed["memories"]:
                        memories.append(MergedMemory(
                            key=mem_data.get("key", ""),
                            value=mem_data.get("value", ""),
                            memory_type=mem_data.get("type", "fact"),
                            confidence=mem_data.get("confidence", "medium"),
                            source="merge_resolver",
                            metadata={
                                "merge_strategy": "resolver",
                                "llm_response": llm_response,
                                "merged_at": datetime.utcnow().isoformat()
                            }
                        ))
                    return memories
            except json.JSONDecodeError:
                pass
            
            # Fallback: use union strategy
            fallback_strategy = AppendLastStrategy(self.db)
            return fallback_strategy._merge_memories_union_newest_wins(source_memories, target_memories)
            
        except Exception as e:
            # Fallback to union strategy if LLM fails
            fallback_strategy = AppendLastStrategy(self.db)
            return fallback_strategy._merge_memories_union_newest_wins(source_memories, target_memories)
    
    def _get_summary_merge_prompt(self) -> str:
        """Get the prompt for summary merging."""
        return """
You are a merge assistant that combines conversation summaries from different branches.

Your task is to merge summaries from a target branch and a source branch into a single, coherent summary.

Guidelines:
1. Preserve all important information from both branches
2. Remove redundancy and overlap
3. Maintain chronological order where relevant
4. Create a unified narrative that flows logically
5. Keep the summary concise but comprehensive

Respond with a JSON object in this format:
{
  "summary": "The merged summary content here..."
}
"""
    
    def _get_memory_merge_prompt(self) -> str:
        """Get the prompt for memory merging."""
        return """
You are a merge assistant that combines conversation memories from different branches.

Your task is to merge memories from a target branch and a source branch, resolving conflicts and deduplicating where appropriate.

Guidelines:
1. Preserve unique memories from both branches
2. Resolve conflicts by choosing the most accurate/complete version
3. Deduplicate similar memories
4. Maintain memory types (fact, preference, context, relationship)
5. Update confidence levels based on agreement between branches

Respond with a JSON object in this format:
{
  "memories": [
    {
      "key": "unique_key",
      "value": "memory content",
      "type": "fact|preference|context|relationship",
      "confidence": "high|medium|low"
    }
  ]
}
"""


class MergeStrategyFactory:
    """Factory for creating merge strategies."""
    
    STRATEGIES = {
        "append-last": AppendLastStrategy,
        "resolver": ResolverStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str, db: Session) -> MergeStrategy:
        """Create a merge strategy by name."""
        strategy_class = cls.STRATEGIES.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown merge strategy: {strategy_name}")
        
        return strategy_class(db)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """List available merge strategies."""
        return list(cls.STRATEGIES.keys())
