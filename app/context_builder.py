from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models import Branch, Message, Thread, Summary, Memory
from app.llm import estimate_tokens


@dataclass
class ContextPolicy:
    """Policy for building conversation context"""
    window_size: int = 50  # Number of recent messages to include
    use_summary: bool = True  # Whether to include thread summary
    use_memory: bool = True  # Whether to include relevant memories
    max_tokens: int = 8000  # Maximum tokens for context
    include_system: bool = True  # Whether to include system messages
    include_metadata: bool = True  # Whether to include message metadata
    memory_relevance_threshold: float = 0.7  # Minimum relevance for memories
    summary_max_length: int = 500  # Maximum summary length in characters


@dataclass
class ConversationContext:
    """Complete conversation context"""
    system: Optional[str] = None
    messages_window: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    memory: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary format"""
        return {
            "system": self.system,
            "messages_window": self.messages_window,
            "summary": self.summary,
            "memory": self.memory,
            "metadata": self.metadata or {}
        }
    
    def get_total_tokens(self) -> int:
        """Estimate total tokens in context"""
        total = 0
        
        if self.system:
            total += estimate_tokens(self.system)
        
        for msg in self.messages_window:
            content = msg.get('content', '')
            if isinstance(content, dict):
                content = content.get('text', '')
            total += estimate_tokens(content)
        
        if self.summary:
            total += estimate_tokens(self.summary)
        
        for memory in self.memory:
            total += estimate_tokens(memory.get('value', ''))
        
        return total


class ContextBuilder:
    """Single source of truth for building conversation context"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_context(
        self, 
        branch_id: str, 
        policy: ContextPolicy = None
    ) -> ConversationContext:
        """
        Build complete conversation context for a branch.
        
        Args:
            branch_id: Branch identifier
            policy: Context building policy
            
        Returns:
            ConversationContext: Complete conversation context
        """
        if policy is None:
            policy = ContextPolicy()
        
        # Get branch and thread information
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        
        thread = self.db.query(Thread).filter(Thread.id == branch.thread_id).first()
        if not thread:
            raise ValueError(f"Thread {branch.thread_id} not found")
        
        # Build context components
        system = self._build_system_context(branch, thread, policy)
        messages_window = self._build_messages_window(branch_id, policy)
        summary = self._build_summary_context(thread.id, policy)
        memory = self._build_memory_context(thread.id, policy)
        metadata = self._build_metadata(branch, thread, policy)
        
        # Create context
        context = ConversationContext(
            system=system,
            messages_window=messages_window,
            summary=summary,
            memory=memory,
            metadata=metadata
        )
        
        # Apply token limits if needed
        if policy.max_tokens > 0:
            context = self._apply_token_limits(context, policy)
        
        return context
    
    def _build_system_context(
        self, 
        branch: Branch, 
        thread: Thread, 
        policy: ContextPolicy
    ) -> Optional[str]:
        """Build system context for the conversation."""
        if not policy.include_system:
            return None
        
        system_parts = []
        
        # Basic system prompt
        system_parts.append("You are a helpful AI assistant in a conversation thread.")
        
        # Thread context
        if thread.title:
            system_parts.append(f"Thread: {thread.title}")
        if thread.description:
            system_parts.append(f"Description: {thread.description}")
        
        # Branch context
        if branch.name and branch.name != "main":
            system_parts.append(f"Current branch: {branch.name}")
        if branch.description:
            system_parts.append(f"Branch context: {branch.description}")
        
        # Forking context
        if branch.created_from_branch_id:
            system_parts.append(f"This branch was forked from another branch.")
        if branch.created_from_message_id:
            system_parts.append(f"This branch was created from a specific message.")
        
        return "\n".join(system_parts) if system_parts else None
    
    def _build_messages_window(
        self, 
        branch_id: str, 
        policy: ContextPolicy
    ) -> List[Dict[str, Any]]:
        """Build messages window for the conversation."""
        # Get recent messages
        query = self.db.query(Message).filter(
            Message.branch_id == branch_id
        ).order_by(Message.created_at.desc())
        
        if not policy.include_system:
            query = query.filter(Message.role != "system")
        
        messages = query.limit(policy.window_size).all()
        messages.reverse()  # Restore chronological order
        
        # Convert to context format
        context_messages = []
        for msg in messages:
            message_data = {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "origin": msg.origin
            }
            
            if policy.include_metadata:
                message_data.update({
                    "parent_message_id": msg.parent_message_id,
                    "state_snapshot": msg.state_snapshot
                })
            
            context_messages.append(message_data)
        
        return context_messages
    
    def _build_summary_context(
        self, 
        thread_id: str, 
        policy: ContextPolicy
    ) -> Optional[str]:
        """Build summary context for the thread."""
        if not policy.use_summary:
            return None
        
        # Get most recent thread summary
        summary = self.db.query(Summary).filter(
            Summary.thread_id == thread_id,
            Summary.summary_type == "thread",
            Summary.is_current == True
        ).order_by(Summary.created_at.desc()).first()
        
        if not summary:
            return None
        
        # Truncate if needed
        content = summary.content
        if len(content) > policy.summary_max_length:
            content = content[:policy.summary_max_length] + "..."
        
        return f"Thread Summary: {content}"
    
    def _build_memory_context(
        self, 
        thread_id: str, 
        policy: ContextPolicy
    ) -> List[Dict[str, Any]]:
        """Build memory context for the thread."""
        if not policy.use_memory:
            return []
        
        # Get relevant memories
        memories = self.db.query(Memory).filter(
            Memory.thread_id == thread_id
        ).all()
        
        # Filter by relevance (simple keyword matching for now)
        relevant_memories = []
        for memory in memories:
            # Simple relevance check - in a real system, you'd use semantic search
            relevance_score = self._calculate_memory_relevance(memory)
            
            if relevance_score >= policy.memory_relevance_threshold:
                relevant_memories.append({
                    "id": memory.id,
                    "type": memory.memory_type,
                    "key": memory.key,
                    "value": memory.value,
                    "confidence": memory.confidence,
                    "source": memory.source,
                    "relevance_score": relevance_score
                })
        
        # Sort by relevance and limit
        relevant_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_memories[:10]  # Limit to top 10 memories
    
    def _calculate_memory_relevance(self, memory: Memory) -> float:
        """Calculate relevance score for a memory."""
        # Simple implementation - in production, use semantic search
        # For now, return a default score based on memory type
        relevance_scores = {
            "fact": 0.8,
            "preference": 0.9,
            "context": 0.7,
            "relationship": 0.6
        }
        
        return relevance_scores.get(memory.memory_type, 0.5)
    
    def _build_metadata(
        self, 
        branch: Branch, 
        thread: Thread, 
        policy: ContextPolicy
    ) -> Dict[str, Any]:
        """Build metadata for the context."""
        if not policy.include_metadata:
            return {}
        
        # Get message count
        message_count = self.db.query(Message).filter(
            Message.branch_id == branch.id
        ).count()
        
        # Get branch count for thread
        branch_count = self.db.query(Branch).filter(
            Branch.thread_id == thread.id
        ).count()
        
        # Get merge count
        merge_count = self.db.query(func.count()).select_from(
            self.db.query(Branch).filter(
                Branch.created_from_branch_id == branch.id
            ).subquery()
        ).scalar()
        
        return {
            "thread_id": thread.id,
            "thread_title": thread.title,
            "branch_id": branch.id,
            "branch_name": branch.name,
            "message_count": message_count,
            "branch_count": branch_count,
            "merge_count": merge_count,
            "created_at": branch.created_at.isoformat(),
            "last_activity": self._get_last_activity(branch.id)
        }
    
    def _get_last_activity(self, branch_id: str) -> Optional[str]:
        """Get last activity timestamp for a branch."""
        last_message = self.db.query(Message).filter(
            Message.branch_id == branch_id
        ).order_by(Message.created_at.desc()).first()
        
        return last_message.created_at.isoformat() if last_message else None
    
    def _apply_token_limits(
        self, 
        context: ConversationContext, 
        policy: ContextPolicy
    ) -> ConversationContext:
        """Apply token limits to context."""
        current_tokens = context.get_total_tokens()
        
        if current_tokens <= policy.max_tokens:
            return context
        
        # Start trimming from least important components
        # 1. Trim memories first
        while context.memory and current_tokens > policy.max_tokens:
            removed_memory = context.memory.pop()
            current_tokens -= estimate_tokens(removed_memory.get('value', ''))
        
        # 2. Trim summary if still over limit
        if context.summary and current_tokens > policy.max_tokens:
            summary_tokens = estimate_tokens(context.summary)
            if summary_tokens > 0:
                # Truncate summary
                target_tokens = summary_tokens - (current_tokens - policy.max_tokens)
                if target_tokens > 0:
                    # Simple truncation - in production, use smarter text truncation
                    context.summary = context.summary[:target_tokens * 4] + "..."
                    current_tokens = context.get_total_tokens()
                else:
                    context.summary = None
                    current_tokens -= summary_tokens
        
        # 3. Trim messages window if still over limit
        while context.messages_window and current_tokens > policy.max_tokens:
            removed_message = context.messages_window.pop(0)  # Remove oldest message
            content = removed_message.get('content', '')
            if isinstance(content, dict):
                content = content.get('text', '')
            current_tokens -= estimate_tokens(content)
        
        return context
    
    def get_context_stats(self, branch_id: str) -> Dict[str, Any]:
        """Get statistics about the context for a branch."""
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        
        # Message count
        message_count = self.db.query(Message).filter(
            Message.branch_id == branch_id
        ).count()
        
        # Summary count
        summary_count = self.db.query(Summary).filter(
            Summary.thread_id == branch.thread_id
        ).count()
        
        # Memory count
        memory_count = self.db.query(Memory).filter(
            Memory.thread_id == branch.thread_id,
            Memory.is_active == True
        ).count()
        
        # Build context with default policy to get token count
        try:
            context = self.build_context(branch_id, ContextPolicy())
            token_count = context.get_total_tokens()
        except Exception:
            token_count = 0
        
        return {
            "branch_id": branch_id,
            "message_count": message_count,
            "summary_count": summary_count,
            "memory_count": memory_count,
            "estimated_tokens": token_count,
            "last_updated": self._get_last_activity(branch_id)
        }


# Predefined context policies
class ContextPolicies:
    """Predefined context building policies"""
    
    @staticmethod
    def minimal() -> ContextPolicy:
        """Minimal context for quick responses"""
        return ContextPolicy(
            window_size=10,
            use_summary=False,
            use_memory=False,
            max_tokens=2000,
            include_system=True,
            include_metadata=False
        )
    
    @staticmethod
    def standard() -> ContextPolicy:
        """Standard context for normal conversations"""
        return ContextPolicy(
            window_size=50,
            use_summary=True,
            use_memory=True,
            max_tokens=8000,
            include_system=True,
            include_metadata=True
        )
    
    @staticmethod
    def comprehensive() -> ContextPolicy:
        """Comprehensive context for complex tasks"""
        return ContextPolicy(
            window_size=100,
            use_summary=True,
            use_memory=True,
            max_tokens=16000,
            include_system=True,
            include_metadata=True,
            memory_relevance_threshold=0.5
        )
    
    @staticmethod
    def summary_only() -> ContextPolicy:
        """Context focused on summaries and memories"""
        return ContextPolicy(
            window_size=5,
            use_summary=True,
            use_memory=True,
            max_tokens=4000,
            include_system=True,
            include_metadata=False
        )
