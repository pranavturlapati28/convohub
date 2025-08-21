from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db import get_db
from app.models import Branch, Message, Merge, Summary, Memory
from app.schemas import MergeRequest, MergeResponse
from app.idempotency import IdempotencyKey, validate_idempotency_key
from app.rate_limiting import rate_limit_middleware
from app.usage_tracker import UsageTracker, RateLimitHeaders
from datetime import datetime

from app.auth import get_current_user, get_current_tenant_context, TenantContext
router = APIRouter(tags=["merges"])

from app.merge_utils import find_lca, path_after, interleave_by_created_at


@router.get(
    "/merge/strategies",
    summary="List available merge strategies",
    description="Get a list of available merge strategies for combining summaries and memories.",
    responses={
        200: {"description": "Strategies retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
def list_merge_strategies():
    """
    List available merge strategies.
    
    Returns:
        List of available merge strategy names and descriptions
    """
    strategies = MergeStrategyFactory.list_strategies()
    
    strategy_descriptions = {
        "append-last": {
            "name": "Append Last",
            "description": "Baseline strategy that concatenates summaries and unions memories with newest-wins conflict resolution",
            "summary_approach": "Concatenate parent summaries with separators",
            "memory_approach": "Union with newest-wins conflict resolution"
        },
        "resolver": {
            "name": "LLM Resolver", 
            "description": "Advanced strategy using LLM to intelligently merge summaries and resolve memory conflicts",
            "summary_approach": "LLM generates coherent merged summary",
            "memory_approach": "LLM resolves conflicts and deduplicates"
        }
    }
    
    return {
        "available_strategies": strategies,
        "strategy_details": {
            strategy: strategy_descriptions.get(strategy, {
                "name": strategy,
                "description": "Strategy details not available"
            })
            for strategy in strategies
        }
    }
from app.merge_strategies import MergeStrategyFactory, MergeContext

@router.post(
    "/merge",
    response_model=MergeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Merge two branches",
    description="Merge a source branch into a target branch. Supports idempotency keys to prevent duplicate merges.",
    responses={
        201: {"description": "Merge completed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
        409: {"description": "Idempotency key conflict"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def merge(
    req: MergeRequest, 
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Merge a source branch into a target branch.
    
    Args:
        req: Merge request data including idempotency key
        db: Database session
        
    Returns:
        MergeResponse: Merge operation result
        
    Raises:
        HTTPException: If merge operation fails
    """
    # Check rate limits and quotas
    current_usage = UsageTracker.get_usage(db, context.tenant_id, "merges_per_day", context.user_id)
    rate_limit_middleware.check_rate_limit_and_quota(
        db, context, "merge", "merges_per_day", current_usage
    )

    # Validate idempotency key
    validate_idempotency_key(req.idempotency_key)
    
    # Check for existing merge with same idempotency key
    idempotency = IdempotencyKey(db, req.idempotency_key, "merge")
    cached_result = idempotency.check_and_lock()
    if cached_result:
        return MergeResponse(**cached_result)

    src = db.get(Branch, req.source_branch_id)
    tgt = db.get(Branch, req.target_branch_id)
    if not src or not tgt or src.thread_id != tgt.thread_id or tgt.thread_id != req.thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Branches must exist and belong to the same thread"
        )

    tgt_tip = db.query(Message).filter(
        Message.branch_id == tgt.id
    ).order_by(Message.created_at.desc()).first()
    src_tip = db.query(Message).filter(
        Message.branch_id == src.id
    ).order_by(Message.created_at.desc()).first()
    
    if not tgt_tip or not src_tip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Both branches must have at least one message"
        )

    lca_id = find_lca(db, src_tip.id, tgt_tip.id)
    a_path = path_after(db, lca_id, src_tip.id) if lca_id else []
    b_path = path_after(db, lca_id, tgt_tip.id) if lca_id else []

    merged_stream = interleave_by_created_at(a_path, b_path)
    diff_summary = {
        "lca": lca_id,
        "src_delta": [m.id for m in a_path],
        "tgt_delta": [m.id for m in b_path],
        "merged_order": [m.id for m in merged_stream],
    }

    parent_id = tgt_tip.id
    merge_commit_id = str(uuid4())
    merge_msg = Message(
        id=merge_commit_id,
        branch_id=tgt.id,
        parent_message_id=parent_id,
        role="assistant",
        content={"text": f"[merge:{req.strategy}] merged {src.id} -> {tgt.id}", "diff": diff_summary},
        state_snapshot={"v": 1, "note": "merged-stub"},
        origin="merge",
        created_at=datetime.utcnow(),
    )
    
    try:
        # Use explicit commit/rollback if no outer transaction, else nest
        if not db.in_transaction():
            transaction_context = db.begin()
        else:
            transaction_context = db.begin_nested()

        with transaction_context:
            db.add(merge_msg)
            db.flush() # Ensure merge_msg is persisted before Merge references it
            
            # Apply merge strategy for summaries and memories
            try:
                merge_strategy = MergeStrategyFactory.create_strategy(req.strategy, db)
                merge_context = MergeContext(
                    thread_id=tgt.thread_id,
                    source_branch_id=src.id,
                    target_branch_id=tgt.id,
                    merge_id=str(uuid4()),
                    db=db
                )
                
                merge_result = merge_strategy.merge_summaries_and_memories(merge_context)
                
                # Save merged summary if created
                if merge_result.summary:
                    merged_summary = Summary(
                        thread_id=tgt.thread_id,
                        summary_type="thread",
                        content=merge_result.summary.content,
                        summary_metadata=merge_result.summary.metadata,
                        is_current=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(merged_summary)
                
                # Save merged memories
                for memory in merge_result.memories:
                    merged_memory = Memory(
                        thread_id=tgt.thread_id,
                        memory_type=memory.memory_type,
                        key=memory.key,
                        value=memory.value,
                        memory_metadata=memory.metadata,
                        confidence=memory.confidence,
                        source=memory.source,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(merged_memory)
                
                # Update merge metadata with strategy results
                diff_summary["merge_strategy_results"] = merge_result.metadata
                
            except Exception as strategy_error:
                # Log strategy error but don't fail the merge
                print(f"Merge strategy failed: {strategy_error}")
                diff_summary["merge_strategy_error"] = str(strategy_error)
            
            m = Merge(
                id=str(uuid4()),
                thread_id=tgt.thread_id,
                source_branch_id=src.id,
                target_branch_id=tgt.id,
                strategy=req.strategy,
                lca_message_id=lca_id,
                merged_into_message_id=merge_commit_id,
                summary=diff_summary,
                created_at=datetime.utcnow(),
            )
            db.add(m)

        # Only commit if this is the outermost transaction
        if not db.in_nested_transaction():
            db.commit()

        # Track usage
        UsageTracker.increment_usage(db, context.tenant_id, "merges_per_day", context.user_id, 1)

        result = MergeResponse(
            merge_id=m.id, 
            merged_into_message_id=merge_commit_id
        )

        # Store result for idempotency
        idempotency.store_result(result.dict())

        return result
        
    except Exception as e:
        # Only rollback if this is the outermost transaction
        if not db.in_nested_transaction():
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge branches: {str(e)}"
        )
