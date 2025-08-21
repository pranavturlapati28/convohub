/**
 * ConvoHub TypeScript SDK Types
 */

export enum DiffMode {
  SUMMARY = 'summary',
  MESSAGES = 'messages',
  MEMORY = 'memory'
}

export interface Thread {
  id: string;
  title: string;
  description?: string;
  owner_id?: string;
  tenant_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Branch {
  id: string;
  thread_id: string;
  name: string;
  description?: string;
  base_message_id?: string;
  created_from_branch_id?: string;
  created_from_message_id?: string;
  is_active: boolean;
  tenant_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Message {
  id: string;
  branch_id: string;
  role: string;
  content: Record<string, any>;
  parent_message_id?: string;
  tenant_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Merge {
  id: string;
  thread_id: string;
  source_branch_id: string;
  target_branch_id: string;
  strategy: string;
  lca_message_id?: string;
  merged_into_message_id?: string;
  conflict_resolution?: Record<string, any>;
  tenant_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MemoryDiff {
  added: Record<string, any>[];
  removed: Record<string, any>[];
  modified: Record<string, any>[];
  conflicts: Record<string, any>[];
}

export interface SummaryDiff {
  left_summary?: string;
  right_summary?: string;
  common_content: string;
  left_only: string;
  right_only: string;
}

export interface MessageRange {
  start_id: string;
  end_id: string;
  count: number;
  messages: Record<string, any>[];
}

export interface DiffResponse {
  lca?: string;
  src_delta: string[];
  tgt_delta: string[];
  merged_order: string[];
  mode: DiffMode;
  memory_diff?: MemoryDiff;
  summary_diff?: SummaryDiff;
  message_ranges?: MessageRange[];
  left_branch_id: string;
  right_branch_id: string;
  diff_timestamp?: string;
}

export interface LoginRequest {
  email: string;
  tenant_domain: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: Record<string, any>;
}

export interface CreateThreadRequest {
  title: string;
  description?: string;
}

export interface CreateBranchRequest {
  name: string;
  description?: string;
  created_from_branch_id?: string;
}

export interface SendMessageRequest {
  role: string;
  text: string;
}

export interface SendMessageResponse {
  user_message_id: string;
  assistant_message_id: string;
}

export interface MergeRequest {
  thread_id: string;
  source_branch_id: string;
  target_branch_id: string;
  strategy: string;
  idempotency_key?: string;
}

export interface ListMessagesResponse {
  messages: Message[];
  next_cursor?: string;
  has_more: boolean;
}

export interface ContextPolicy {
  window_size?: number;
  use_summary?: boolean;
  use_memory?: boolean;
  max_tokens?: number;
  system_messages?: string[];
  metadata?: Record<string, any>;
  relevance_threshold?: number;
}

export interface ConversationContext {
  system: string;
  messages_window: Record<string, any>[];
  summary?: string;
  memory: Record<string, any>[];
  metadata: Record<string, any>;
}
