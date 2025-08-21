/**
 * ConvoHub TypeScript SDK Models
 * 
 * Model classes and utilities for the ConvoHub API.
 */

import {
  Thread,
  Branch,
  Message,
  Merge,
  DiffResponse,
  DiffMode,
  MemoryDiff,
  SummaryDiff,
  MessageRange,
  LoginRequest,
  LoginResponse,
  CreateThreadRequest,
  CreateBranchRequest,
  SendMessageRequest,
  SendMessageResponse,
  MergeRequest,
  ListMessagesResponse,
  ContextPolicy,
  ConversationContext
} from './types';

// Re-export all types as models
export {
  Thread,
  Branch,
  Message,
  Merge,
  DiffResponse,
  DiffMode,
  MemoryDiff,
  SummaryDiff,
  MessageRange,
  LoginRequest,
  LoginResponse,
  CreateThreadRequest,
  CreateBranchRequest,
  SendMessageRequest,
  SendMessageResponse,
  MergeRequest,
  ListMessagesResponse,
  ContextPolicy,
  ConversationContext
};

// Model factory functions for creating instances
export class ModelFactory {
  /**
   * Create a Thread instance
   */
  static createThread(data: Partial<Thread>): Thread {
    return {
      id: data.id || '',
      title: data.title || '',
      description: data.description,
      owner_id: data.owner_id,
      tenant_id: data.tenant_id,
      created_at: data.created_at,
      updated_at: data.updated_at,
    };
  }

  /**
   * Create a Branch instance
   */
  static createBranch(data: Partial<Branch>): Branch {
    return {
      id: data.id || '',
      thread_id: data.thread_id || '',
      name: data.name || '',
      description: data.description,
      base_message_id: data.base_message_id,
      created_from_branch_id: data.created_from_branch_id,
      created_from_message_id: data.created_from_message_id,
      is_active: data.is_active ?? true,
      tenant_id: data.tenant_id,
      created_at: data.created_at,
      updated_at: data.updated_at,
    };
  }

  /**
   * Create a Message instance
   */
  static createMessage(data: Partial<Message>): Message {
    return {
      id: data.id || '',
      branch_id: data.branch_id || '',
      role: data.role || 'user',
      content: data.content || {},
      parent_message_id: data.parent_message_id,
      tenant_id: data.tenant_id,
      created_at: data.created_at,
      updated_at: data.updated_at,
    };
  }

  /**
   * Create a Merge instance
   */
  static createMerge(data: Partial<Merge>): Merge {
    return {
      id: data.id || '',
      thread_id: data.thread_id || '',
      source_branch_id: data.source_branch_id || '',
      target_branch_id: data.target_branch_id || '',
      strategy: data.strategy || 'append-last',
      lca_message_id: data.lca_message_id,
      merged_into_message_id: data.merged_into_message_id,
      conflict_resolution: data.conflict_resolution,
      tenant_id: data.tenant_id,
      created_at: data.created_at,
      updated_at: data.updated_at,
    };
  }

  /**
   * Create a DiffResponse instance
   */
  static createDiffResponse(data: Partial<DiffResponse>): DiffResponse {
    return {
      lca: data.lca,
      src_delta: data.src_delta || [],
      tgt_delta: data.tgt_delta || [],
      merged_order: data.merged_order || [],
      mode: data.mode || DiffMode.MESSAGES,
      memory_diff: data.memory_diff,
      summary_diff: data.summary_diff,
      message_ranges: data.message_ranges,
      left_branch_id: data.left_branch_id || '',
      right_branch_id: data.right_branch_id || '',
      diff_timestamp: data.diff_timestamp,
    };
  }

  /**
   * Create a MemoryDiff instance
   */
  static createMemoryDiff(data: Partial<MemoryDiff>): MemoryDiff {
    return {
      added: data.added || [],
      removed: data.removed || [],
      modified: data.modified || [],
      conflicts: data.conflicts || [],
    };
  }

  /**
   * Create a SummaryDiff instance
   */
  static createSummaryDiff(data: Partial<SummaryDiff>): SummaryDiff {
    return {
      left_summary: data.left_summary,
      right_summary: data.right_summary,
      common_content: data.common_content || '',
      left_only: data.left_only || '',
      right_only: data.right_only || '',
    };
  }

  /**
   * Create a MessageRange instance
   */
  static createMessageRange(data: Partial<MessageRange>): MessageRange {
    return {
      start_id: data.start_id || '',
      end_id: data.end_id || '',
      count: data.count || 0,
      messages: data.messages || [],
    };
  }
}
