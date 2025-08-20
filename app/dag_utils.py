from typing import List, Set, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models import Message, Edge

class DAGValidator:
    """Validates and maintains DAG structure for messages"""
    
    @staticmethod
    def validate_no_cycles(db: Session, message_id: str, parent_ids: List[str]) -> bool:
        """
        Validate that adding the specified parent relationships won't create cycles.
        
        Args:
            db: Database session
            message_id: ID of the message being validated
            parent_ids: List of parent message IDs to check
            
        Returns:
            bool: True if no cycles would be created
            
        Raises:
            HTTPException: If cycles would be created
        """
        # Check if any parent would create a cycle
        for parent_id in parent_ids:
            if DAGValidator._would_create_cycle(db, message_id, parent_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Adding parent {parent_id} would create a cycle in the message DAG"
                )
        return True
    
    @staticmethod
    def _would_create_cycle(db: Session, message_id: str, parent_id: str) -> bool:
        """
        Check if adding a parent relationship would create a cycle.
        
        Args:
            db: Database session
            message_id: ID of the message
            parent_id: ID of the potential parent
            
        Returns:
            bool: True if adding this parent would create a cycle
        """
        # If the parent is the same as the message, that's a cycle
        if message_id == parent_id:
            return True
            
        # Check if the parent is a descendant of the message
        return DAGValidator._is_descendant(db, parent_id, message_id)
    
    @staticmethod
    def _is_descendant(db: Session, ancestor_id: str, descendant_id: str) -> bool:
        """
        Check if descendant_id is a descendant of ancestor_id.
        
        Args:
            db: Database session
            ancestor_id: ID of the potential ancestor
            descendant_id: ID of the potential descendant
            
        Returns:
            bool: True if descendant_id is a descendant of ancestor_id
        """
        visited = set()
        return DAGValidator._dfs_check_descendant(db, ancestor_id, descendant_id, visited)
    
    @staticmethod
    def _dfs_check_descendant(db: Session, current_id: str, target_id: str, visited: Set[str]) -> bool:
        """
        DFS to check if target_id is reachable from current_id.
        
        Args:
            db: Database session
            current_id: Current message ID being checked
            target_id: Target message ID to find
            visited: Set of visited message IDs
            
        Returns:
            bool: True if target_id is reachable from current_id
        """
        if current_id in visited:
            return False
            
        visited.add(current_id)
        
        if current_id == target_id:
            return True
            
        # Check direct children via parent_message_id
        children = db.query(Message).filter(Message.parent_message_id == current_id).all()
        for child in children:
            if DAGValidator._dfs_check_descendant(db, child.id, target_id, visited):
                return True
                
        # Check children via edges table
        edges = db.query(Edge).filter(Edge.from_message_id == current_id).all()
        for edge in edges:
            if DAGValidator._dfs_check_descendant(db, edge.to_message_id, target_id, visited):
                return True
                
        return False
    
    @staticmethod
    def get_ancestors(db: Session, message_id: str) -> List[Message]:
        """
        Get all ancestors of a message.
        
        Args:
            db: Database session
            message_id: ID of the message
            
        Returns:
            List[Message]: List of ancestor messages
        """
        ancestors = []
        visited = set()
        DAGValidator._collect_ancestors(db, message_id, ancestors, visited)
        return ancestors
    
    @staticmethod
    def _collect_ancestors(db: Session, message_id: str, ancestors: List[Message], visited: Set[str]):
        """
        Recursively collect all ancestors of a message.
        
        Args:
            db: Database session
            message_id: ID of the message
            ancestors: List to collect ancestors
            visited: Set of visited message IDs
        """
        if message_id in visited:
            return
            
        visited.add(message_id)
        
        # Get direct parent
        message = db.get(Message, message_id)
        if message and message.parent_message_id:
            parent = db.get(Message, message.parent_message_id)
            if parent and parent.id not in visited:
                ancestors.append(parent)
                DAGValidator._collect_ancestors(db, parent.id, ancestors, visited)
        
        # Get parents via edges
        edges = db.query(Edge).filter(Edge.to_message_id == message_id).all()
        for edge in edges:
            parent = db.get(Message, edge.from_message_id)
            if parent and parent.id not in visited:
                ancestors.append(parent)
                DAGValidator._collect_ancestors(db, parent.id, ancestors, visited)
    
    @staticmethod
    def get_descendants(db: Session, message_id: str) -> List[Message]:
        """
        Get all descendants of a message.
        
        Args:
            db: Database session
            message_id: ID of the message
            
        Returns:
            List[Message]: List of descendant messages
        """
        descendants = []
        visited = set()
        DAGValidator._collect_descendants(db, message_id, descendants, visited)
        return descendants
    
    @staticmethod
    def _collect_descendants(db: Session, message_id: str, descendants: List[Message], visited: Set[str]):
        """
        Recursively collect all descendants of a message.
        
        Args:
            db: Database session
            message_id: ID of the message
            descendants: List to collect descendants
            visited: Set of visited message IDs
        """
        if message_id in visited:
            return
            
        visited.add(message_id)
        
        # Get direct children
        children = db.query(Message).filter(Message.parent_message_id == message_id).all()
        for child in children:
            if child.id not in visited:
                descendants.append(child)
                DAGValidator._collect_descendants(db, child.id, descendants, visited)
        
        # Get children via edges
        edges = db.query(Edge).filter(Edge.from_message_id == message_id).all()
        for edge in edges:
            child = db.get(Message, edge.to_message_id)
            if child and child.id not in visited:
                descendants.append(child)
                DAGValidator._collect_descendants(db, child.id, descendants, visited)


class EdgeManager:
    """Manages explicit edges in the message DAG"""
    
    @staticmethod
    def add_edge(db: Session, from_message_id: str, to_message_id: str, 
                edge_type: str = "parent", weight: Optional[str] = None) -> Edge:
        """
        Add an edge between two messages.
        
        Args:
            db: Database session
            from_message_id: Source message ID
            to_message_id: Target message ID
            edge_type: Type of edge (parent, merge_parent, reference)
            weight: Optional weight for the edge
            
        Returns:
            Edge: Created edge
            
        Raises:
            HTTPException: If edge creation would violate DAG constraints
        """
        # Validate edge type
        if edge_type not in ["parent", "merge_parent", "reference"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid edge type: {edge_type}"
            )
        
        # Check for cycles
        DAGValidator.validate_no_cycles(db, to_message_id, [from_message_id])
        
        # Create edge
        edge = Edge(
            from_message_id=from_message_id,
            to_message_id=to_message_id,
            edge_type=edge_type,
            weight=weight
        )
        
        try:
            db.add(edge)
            db.commit()
            return edge
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Edge already exists between these messages"
            )
    
    @staticmethod
    def remove_edge(db: Session, from_message_id: str, to_message_id: str) -> bool:
        """
        Remove an edge between two messages.
        
        Args:
            db: Database session
            from_message_id: Source message ID
            to_message_id: Target message ID
            
        Returns:
            bool: True if edge was removed
        """
        edge = db.query(Edge).filter(
            Edge.from_message_id == from_message_id,
            Edge.to_message_id == to_message_id
        ).first()
        
        if edge:
            db.delete(edge)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_edges(db: Session, message_id: str, direction: str = "both") -> List[Edge]:
        """
        Get edges for a message.
        
        Args:
            db: Database session
            message_id: ID of the message
            direction: "in", "out", or "both"
            
        Returns:
            List[Edge]: List of edges
        """
        query = db.query(Edge)
        
        if direction == "in":
            query = query.filter(Edge.to_message_id == message_id)
        elif direction == "out":
            query = query.filter(Edge.from_message_id == message_id)
        elif direction == "both":
            query = query.filter(
                (Edge.from_message_id == message_id) | 
                (Edge.to_message_id == message_id)
            )
        else:
            raise ValueError("Direction must be 'in', 'out', or 'both'")
            
        return query.all()
