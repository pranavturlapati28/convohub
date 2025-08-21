"""
ConvoHub Python SDK Client

Main client for interacting with the ConvoHub API.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import (
    Thread, Branch, Message, Merge, DiffResponse,
    DiffMode, MemoryDiff, SummaryDiff, MessageRange
)


class ConvoHubClient:
    """ConvoHub API client"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: Optional[str] = None):
        """
        Initialize the ConvoHub client.
        
        Args:
            base_url: Base URL for the ConvoHub API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def login(self, email: str, tenant_domain: str, password: str) -> str:
        """
        Authenticate and get access token.
        
        Args:
            email: User email
            tenant_domain: Tenant domain
            password: User password
            
        Returns:
            Access token
        """
        data = {
            "email": email,
            "tenant_domain": tenant_domain,
            "password": password
        }
        
        response = self._make_request("POST", "/v1/auth/login", json=data)
        token = response["access_token"]
        
        # Update session with new token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return token
    
    def create_thread(self, title: str, description: Optional[str] = None) -> Thread:
        """
        Create a new thread.
        
        Args:
            title: Thread title
            description: Optional thread description
            
        Returns:
            Created thread
        """
        data = {"title": title}
        if description:
            data["description"] = description
            
        response = self._make_request("POST", "/v1/threads", json=data)
        return Thread(**response)
    
    def create_branch(self, thread_id: str, name: str, description: Optional[str] = None,
                     created_from_branch_id: Optional[str] = None) -> Branch:
        """
        Create a new branch.
        
        Args:
            thread_id: Parent thread ID
            name: Branch name
            description: Optional branch description
            created_from_branch_id: Optional source branch ID
            
        Returns:
            Created branch
        """
        data = {"name": name}
        if description:
            data["description"] = description
        if created_from_branch_id:
            data["created_from_branch_id"] = created_from_branch_id
            
        response = self._make_request("POST", f"/v1/threads/{thread_id}/branches", json=data)
        return Branch(**response)
    
    def send_message(self, branch_id: str, role: str, text: str) -> Dict[str, str]:
        """
        Send a message to a branch.
        
        Args:
            branch_id: Target branch ID
            role: Message role (user, assistant, system)
            text: Message text
            
        Returns:
            Dictionary with user_message_id and assistant_message_id
        """
        data = {
            "role": role,
            "text": text
        }
        
        response = self._make_request("POST", f"/v1/branches/{branch_id}/messages", json=data)
        return response
    
    def list_messages(self, branch_id: str, cursor: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        List messages in a branch.
        
        Args:
            branch_id: Branch ID
            cursor: Optional pagination cursor
            limit: Maximum number of messages to return
            
        Returns:
            Paginated messages response
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
            
        return self._make_request("GET", f"/v1/branches/{branch_id}/messages", params=params)
    
    def merge(self, thread_id: str, source_branch_id: str, target_branch_id: str,
              strategy: str = "append-last", idempotency_key: Optional[str] = None) -> Merge:
        """
        Merge two branches.
        
        Args:
            thread_id: Thread ID
            source_branch_id: Source branch ID
            target_branch_id: Target branch ID
            strategy: Merge strategy (append-last, resolver, etc.)
            idempotency_key: Optional idempotency key
            
        Returns:
            Merge result
        """
        data = {
            "thread_id": thread_id,
            "source_branch_id": source_branch_id,
            "target_branch_id": target_branch_id,
            "strategy": strategy
        }
        
        params = {}
        if idempotency_key:
            params["idempotency_key"] = idempotency_key
            
        response = self._make_request("POST", "/v1/merge", json=data, params=params)
        return Merge(**response)
    
    def diff(self, left_branch_id: str, right_branch_id: str, mode: DiffMode = DiffMode.MESSAGES) -> DiffResponse:
        """
        Compare two branches.
        
        Args:
            left_branch_id: Left branch ID
            right_branch_id: Right branch ID
            mode: Diff mode (summary, messages, memory)
            
        Returns:
            Diff response
        """
        params = {
            "left": left_branch_id,
            "right": right_branch_id,
            "mode": mode.value
        }
        
        response = self._make_request("GET", "/v1/diff", params=params)
        
        # Convert nested objects
        if response.get("memory_diff"):
            response["memory_diff"] = MemoryDiff(**response["memory_diff"])
        if response.get("summary_diff"):
            response["summary_diff"] = SummaryDiff(**response["summary_diff"])
        if response.get("message_ranges"):
            response["message_ranges"] = [MessageRange(**r) for r in response["message_ranges"]]
        
        return DiffResponse(**response)
    
    def diff_memory(self, left_branch_id: str, right_branch_id: str) -> DiffResponse:
        """Three-way memory diff between branches"""
        return self.diff(left_branch_id, right_branch_id, DiffMode.MEMORY)
    
    def diff_summary(self, left_branch_id: str, right_branch_id: str) -> DiffResponse:
        """Summary diff between branches"""
        return self.diff(left_branch_id, right_branch_id, DiffMode.SUMMARY)
    
    def diff_messages(self, left_branch_id: str, right_branch_id: str) -> DiffResponse:
        """Message ranges diff between branches"""
        return self.diff(left_branch_id, right_branch_id, DiffMode.MESSAGES)
    
    def get_context(self, branch_id: str, policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get conversation context for a branch.
        
        Args:
            branch_id: Branch ID
            policy: Optional context policy
            
        Returns:
            Conversation context
        """
        params = {}
        if policy:
            params["policy"] = json.dumps(policy)
            
        return self._make_request("GET", f"/v1/context/{branch_id}", params=params)
    
    def get_summaries(self, thread_id: str) -> Dict[str, Any]:
        """Get summaries for a thread"""
        return self._make_request("GET", f"/v1/threads/{thread_id}/summaries")
    
    def get_memories(self, thread_id: str) -> Dict[str, Any]:
        """Get memories for a thread"""
        return self._make_request("GET", f"/v1/threads/{thread_id}/memories")
