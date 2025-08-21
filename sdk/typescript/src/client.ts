/**
 * ConvoHub TypeScript SDK Client
 * 
 * Main client for interacting with the ConvoHub API.
 */

import {
  Thread,
  Branch,
  Message,
  Merge,
  DiffResponse,
  DiffMode,
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

export class ConvoHubClient {
  private baseUrl: string;
  private apiKey?: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string = 'http://127.0.0.1:8000', apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.headers = {
      'Content-Type': 'application/json',
    };

    if (apiKey) {
      this.headers['Authorization'] = `Bearer ${apiKey}`;
    }
  }

  private async makeRequest<T>(
    method: string,
    endpoint: string,
    body?: any,
    params?: Record<string, any>
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method,
      headers: this.headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Authenticate and get access token.
   */
  async login(email: string, tenantDomain: string, password: string): Promise<string> {
    const request: LoginRequest = {
      email,
      tenant_domain: tenantDomain,
      password,
    };

    const response: LoginResponse = await this.makeRequest('POST', '/v1/auth/login', request);
    
    // Update headers with new token
    this.headers['Authorization'] = `Bearer ${response.access_token}`;
    
    return response.access_token;
  }

  /**
   * Create a new thread.
   */
  async createThread(title: string, description?: string): Promise<Thread> {
    const request: CreateThreadRequest = { title };
    if (description) {
      request.description = description;
    }

    return this.makeRequest<Thread>('POST', '/v1/threads', request);
  }

  /**
   * Create a new branch.
   */
  async createBranch(
    threadId: string,
    name: string,
    description?: string,
    createdFromBranchId?: string
  ): Promise<Branch> {
    const request: CreateBranchRequest = { name };
    if (description) {
      request.description = description;
    }
    if (createdFromBranchId) {
      request.created_from_branch_id = createdFromBranchId;
    }

    return this.makeRequest<Branch>('POST', `/v1/threads/${threadId}/branches`, request);
  }

  /**
   * Send a message to a branch.
   */
  async sendMessage(branchId: string, role: string, text: string): Promise<SendMessageResponse> {
    const request: SendMessageRequest = { role, text };
    return this.makeRequest<SendMessageResponse>('POST', `/v1/branches/${branchId}/messages`, request);
  }

  /**
   * List messages in a branch.
   */
  async listMessages(
    branchId: string,
    cursor?: string,
    limit: number = 50
  ): Promise<ListMessagesResponse> {
    const params: Record<string, any> = { limit };
    if (cursor) {
      params.cursor = cursor;
    }

    return this.makeRequest<ListMessagesResponse>('GET', `/v1/branches/${branchId}/messages`, undefined, params);
  }

  /**
   * Merge two branches.
   */
  async merge(
    threadId: string,
    sourceBranchId: string,
    targetBranchId: string,
    strategy: string = 'append-last',
    idempotencyKey?: string
  ): Promise<Merge> {
    const request: MergeRequest = {
      thread_id: threadId,
      source_branch_id: sourceBranchId,
      target_branch_id: targetBranchId,
      strategy,
    };

    const params: Record<string, any> = {};
    if (idempotencyKey) {
      params.idempotency_key = idempotencyKey;
    }

    return this.makeRequest<Merge>('POST', '/v1/merge', request, params);
  }

  /**
   * Compare two branches.
   */
  async diff(
    leftBranchId: string,
    rightBranchId: string,
    mode: DiffMode = DiffMode.MESSAGES
  ): Promise<DiffResponse> {
    const params = {
      left: leftBranchId,
      right: rightBranchId,
      mode,
    };

    return this.makeRequest<DiffResponse>('GET', '/v1/diff', undefined, params);
  }

  /**
   * Three-way memory diff between branches.
   */
  async diffMemory(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    return this.diff(leftBranchId, rightBranchId, DiffMode.MEMORY);
  }

  /**
   * Summary diff between branches.
   */
  async diffSummary(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    return this.diff(leftBranchId, rightBranchId, DiffMode.SUMMARY);
  }

  /**
   * Message ranges diff between branches.
   */
  async diffMessages(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    return this.diff(leftBranchId, rightBranchId, DiffMode.MESSAGES);
  }

  /**
   * Get conversation context for a branch.
   */
  async getContext(branchId: string, policy?: ContextPolicy): Promise<ConversationContext> {
    const params: Record<string, any> = {};
    if (policy) {
      params.policy = JSON.stringify(policy);
    }

    return this.makeRequest<ConversationContext>('GET', `/v1/context/${branchId}`, undefined, params);
  }

  /**
   * Get summaries for a thread.
   */
  async getSummaries(threadId: string): Promise<Record<string, any>> {
    return this.makeRequest<Record<string, any>>('GET', `/v1/threads/${threadId}/summaries`);
  }

  /**
   * Get memories for a thread.
   */
  async getMemories(threadId: string): Promise<Record<string, any>> {
    return this.makeRequest<Record<string, any>>('GET', `/v1/threads/${threadId}/memories`);
  }
}
