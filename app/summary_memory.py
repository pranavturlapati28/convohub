from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models import Thread, Message, Summary, Memory, Branch
from app.llm import estimate_tokens
import re
import json


class SummaryMemoryManager:
    """Manages automatic summary and memory updates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_after_assistant_message(
        self, 
        thread_id: str, 
        branch_id: str,
        assistant_message: Message,
        target_summary_tokens: int = 200
    ) -> Tuple[Optional[Summary], List[Memory]]:
        """
        Update rolling summary and extract structured memory after assistant message.
        
        Args:
            thread_id: Thread identifier
            branch_id: Branch identifier  
            assistant_message: The assistant message that was just sent
            target_summary_tokens: Target length for summary in tokens
            
        Returns:
            Tuple of (updated_summary, new_memories)
        """
        # Get recent conversation context
        recent_messages = self._get_recent_messages(branch_id, limit=20)
        
        # Update rolling summary
        updated_summary = self._update_rolling_summary(
            thread_id, recent_messages, target_summary_tokens
        )
        
        # Extract structured memory from the assistant message
        new_memories = self._extract_structured_memory(
            thread_id, assistant_message, recent_messages
        )
        
        return updated_summary, new_memories
    
    def _get_recent_messages(self, branch_id: str, limit: int = 20) -> List[Message]:
        """Get recent messages for context building."""
        return (self.db.query(Message)
                .filter(Message.branch_id == branch_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all())
    
    def _update_rolling_summary(
        self, 
        thread_id: str, 
        recent_messages: List[Message],
        target_tokens: int
    ) -> Optional[Summary]:
        """
        Update rolling summary based on recent messages.
        
        Strategy:
        1. Get current summary if it exists
        2. Analyze recent messages for new information
        3. Merge new info into summary, keeping within token limit
        4. Save updated summary
        """
        # Get current summary
        current_summary = (self.db.query(Summary)
                          .filter(
                              Summary.thread_id == thread_id,
                              Summary.summary_type == "thread",
                              Summary.is_current == True
                          )
                          .first())
        
        # Build conversation text from recent messages
        conversation_text = self._build_conversation_text(recent_messages)
        
        # Generate new summary
        new_summary_text = self._generate_rolling_summary(
            current_summary.content if current_summary else "",
            conversation_text,
            target_tokens
        )
        
        if not new_summary_text:
            return current_summary
        
        # Mark current summary as not current
        if current_summary:
            current_summary.is_current = False
            current_summary.updated_at = datetime.utcnow()
        
        # Create new summary
        new_summary = Summary(
            thread_id=thread_id,
            summary_type="thread",
            content=new_summary_text,
            summary_metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "target_tokens": target_tokens,
                "message_count": len(recent_messages),
                "version": "1.0"
            },
            is_current=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(new_summary)
        self.db.flush()
        
        return new_summary
    
    def _build_conversation_text(self, messages: List[Message]) -> str:
        """Build conversation text from messages."""
        conversation_parts = []
        
        for msg in reversed(messages):  # Reverse to get chronological order
            role = msg.role
            content = msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content)
            
            if role == 'user':
                conversation_parts.append(f"User: {content}")
            elif role == 'assistant':
                conversation_parts.append(f"Assistant: {content}")
            elif role == 'system':
                conversation_parts.append(f"System: {content}")
        
        return "\n".join(conversation_parts)
    
    def _generate_rolling_summary(
        self, 
        current_summary: str, 
        new_conversation: str,
        target_tokens: int
    ) -> str:
        """
        Generate rolling summary by merging current summary with new conversation.
        
        This is a simple implementation. In production, you'd use an LLM to:
        1. Analyze the new conversation for key information
        2. Determine what to add/update in the summary
        3. Generate a coherent summary within token limits
        """
        # For now, use a simple approach: combine and truncate
        combined = f"{current_summary}\n\nRecent conversation:\n{new_conversation}"
        
        # Simple truncation to target tokens (roughly 4 chars per token)
        target_chars = target_tokens * 4
        
        if len(combined) <= target_chars:
            return combined
        
        # Truncate and add ellipsis
        truncated = combined[:target_chars-3] + "..."
        
        # Try to end at a sentence boundary
        last_period = truncated.rfind('.')
        if last_period > target_chars * 0.8:  # If we can end at a sentence
            return truncated[:last_period+1]
        
        return truncated
    
    def _extract_structured_memory(
        self, 
        thread_id: str, 
        assistant_message: Message,
        recent_messages: List[Message]
    ) -> List[Memory]:
        """
        Extract structured memory from assistant message and conversation context.
        
        Looks for:
        - Facts mentioned by the assistant
        - User preferences expressed
        - Contextual information
        - Relationships between topics
        """
        new_memories = []
        
        # Get assistant message content
        content = assistant_message.content.get('text', '') if isinstance(assistant_message.content, dict) else str(assistant_message.content)
        
        # Extract facts (simple pattern matching for now)
        facts = self._extract_facts(content)
        for i, fact in enumerate(facts):
            memory = Memory(
                thread_id=thread_id,
                memory_type="fact",
                key=f"fact_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{i}",
                value=fact,
                memory_metadata={
                    "source": "assistant_message",
                    "message_id": assistant_message.id,
                    "extracted_at": datetime.utcnow().isoformat()
                },
                confidence="high",
                source="pattern_extraction",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_memories.append(memory)
        
        # Extract user preferences from recent conversation
        preferences = self._extract_preferences(recent_messages)
        for i, pref in enumerate(preferences):
            memory = Memory(
                thread_id=thread_id,
                memory_type="preference",
                key=f"preference_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{i}",
                value=pref,
                memory_metadata={
                    "source": "conversation_analysis",
                    "extracted_at": datetime.utcnow().isoformat()
                },
                confidence="medium",
                source="conversation_analysis",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_memories.append(memory)
        
        # Extract contextual information
        context = self._extract_context(recent_messages)
        if context:
            memory = Memory(
                thread_id=thread_id,
                memory_type="context",
                key=f"conversation_context_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                value=context,
                memory_metadata={
                    "source": "conversation_analysis",
                    "extracted_at": datetime.utcnow().isoformat()
                },
                confidence="medium",
                source="conversation_analysis",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            new_memories.append(memory)
        
        # Save new memories
        for memory in new_memories:
            self.db.add(memory)
        
        self.db.flush()
        
        return new_memories
    
    def _extract_facts(self, content: str) -> List[str]:
        """Extract facts from assistant message content."""
        facts = []
        
        # Simple fact extraction patterns
        fact_patterns = [
            r'([A-Z][^.!?]*?(?:is|are|was|were|has|have|can|will|should|must)[^.!?]*[.!?])',
            r'([A-Z][^.!?]*?(?:fact|information|data|statistic)[^.!?]*[.!?])',
            r'([A-Z][^.!?]*?(?:according to|research shows|studies indicate)[^.!?]*[.!?])'
        ]
        
        for pattern in fact_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            facts.extend(matches)
        
        # Remove duplicates and clean up
        facts = list(set(facts))
        facts = [fact.strip() for fact in facts if len(fact.strip()) > 20]
        
        return facts[:5]  # Limit to 5 facts
    
    def _extract_preferences(self, messages: List[Message]) -> List[str]:
        """Extract user preferences from conversation."""
        preferences = []
        
        for msg in messages:
            if msg.role != 'user':
                continue
                
            content = msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content)
            
            # Look for preference indicators
            preference_patterns = [
                r'(?:I prefer|I like|I want|I need|I would like|I enjoy|I hate|I dislike)[^.!?]*[.!?]',
                r'(?:favorite|best|worst|better|worse)[^.!?]*[.!?]',
                r'(?:always|never|usually|sometimes)[^.!?]*[.!?]'
            ]
            
            for pattern in preference_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                preferences.extend(matches)
        
        # Clean up and deduplicate
        preferences = list(set(preferences))
        preferences = [pref.strip() for pref in preferences if len(pref.strip()) > 10]
        
        return preferences[:3]  # Limit to 3 preferences
    
    def _extract_context(self, messages: List[Message]) -> Optional[str]:
        """Extract contextual information from conversation."""
        context_parts = []
        
        # Look for contextual clues
        for msg in messages:
            if msg.role != 'user':
                continue
                
            content = msg.content.get('text', '') if isinstance(msg.content, dict) else str(msg.content)
            
            # Look for context indicators
            context_patterns = [
                r'(?:I am|I\'m|I work|I study|I live|I\'m from)[^.!?]*[.!?]',
                r'(?:currently|now|today|this week|this month)[^.!?]*[.!?]',
                r'(?:project|work|study|research|task)[^.!?]*[.!?]'
            ]
            
            for pattern in context_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                context_parts.extend(matches)
        
        if not context_parts:
            return None
        
        # Combine context parts
        context = " ".join(context_parts[:3])  # Limit to 3 context pieces
        return context.strip()
