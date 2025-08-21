import axios, { AxiosInstance } from 'axios'
import {
  Thread,
  Branch,
  Message,
  Merge,
  DiffResponse,
  LoginRequest,
  LoginResponse,
  CreateThreadRequest,
  CreateBranchRequest,
  SendMessageRequest,
  SendMessageResponse,
  MergeRequest,
  ListMessagesResponse,
  ContextPolicy,
  ConversationContext,
  ThreadSummariesResponse,
  ThreadMemoriesResponse,
} from '@/types/api'

class ConvoHubAPI {
  private client: AxiosInstance
  private token: string | null = null

  constructor(baseURL: string = 'http://127.0.0.1:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }
      return config
    })
  }

  setToken(token: string) {
    this.token = token
  }

  clearToken() {
    this.token = null
  }

  // Authentication
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/v1/auth/login', request)
    this.setToken(response.data.access_token)
    return response.data
  }

  // Threads
  async createThread(request: CreateThreadRequest): Promise<Thread> {
    const response = await this.client.post<Thread>('/v1/threads', request)
    return response.data
  }

  async getThreadSummaries(threadId: string): Promise<ThreadSummariesResponse> {
    const response = await this.client.get<ThreadSummariesResponse>(
      `/v1/threads/${threadId}/summaries`
    )
    return response.data
  }

  async getThreadMemories(threadId: string): Promise<ThreadMemoriesResponse> {
    const response = await this.client.get<ThreadMemoriesResponse>(
      `/v1/threads/${threadId}/memories`
    )
    return response.data
  }

  // Branches
  async createBranch(
    threadId: string,
    request: CreateBranchRequest
  ): Promise<Branch> {
    const response = await this.client.post<Branch>(
      `/v1/threads/${threadId}/branches`,
      request
    )
    return response.data
  }

  // Messages
  async sendMessage(
    branchId: string,
    request: SendMessageRequest,
    idempotencyKey?: string
  ): Promise<SendMessageResponse> {
    const params = idempotencyKey ? { idempotency_key: idempotencyKey } : {}
    const response = await this.client.post<SendMessageResponse>(
      `/v1/branches/${branchId}/messages`,
      request,
      { params }
    )
    return response.data
  }

  async listMessages(
    branchId: string,
    cursor?: string,
    limit: number = 50
  ): Promise<ListMessagesResponse> {
    const params: Record<string, any> = { limit }
    if (cursor) params.cursor = cursor

    const response = await this.client.get<ListMessagesResponse>(
      `/v1/branches/${branchId}/messages`,
      { params }
    )
    return response.data
  }

  // Merge
  async merge(request: MergeRequest): Promise<Merge> {
    const params: Record<string, any> = {}
    if (request.idempotency_key) params.idempotency_key = request.idempotency_key

    const response = await this.client.post<Merge>('/v1/merge', request, {
      params,
    })
    return response.data
  }

  async getMergeStrategies(): Promise<string[]> {
    const response = await this.client.get<string[]>('/v1/merge/strategies')
    return response.data
  }

  // Diff
  async diff(
    leftBranchId: string,
    rightBranchId: string,
    mode: 'summary' | 'messages' | 'memory' = 'messages'
  ): Promise<DiffResponse> {
    const response = await this.client.get<DiffResponse>('/v1/diff', {
      params: {
        left: leftBranchId,
        right: rightBranchId,
        mode,
      },
    })
    return response.data
  }

  async diffMemory(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    const response = await this.client.get<DiffResponse>('/v1/diff/memory', {
      params: {
        left: leftBranchId,
        right: rightBranchId,
      },
    })
    return response.data
  }

  async diffSummary(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    const response = await this.client.get<DiffResponse>('/v1/diff/summary', {
      params: {
        left: leftBranchId,
        right: rightBranchId,
      },
    })
    return response.data
  }

  async diffMessages(leftBranchId: string, rightBranchId: string): Promise<DiffResponse> {
    const response = await this.client.get<DiffResponse>('/v1/diff/messages', {
      params: {
        left: leftBranchId,
        right: rightBranchId,
      },
    })
    return response.data
  }

  // Context
  async getContext(
    branchId: string,
    policy?: ContextPolicy
  ): Promise<ConversationContext> {
    const params: Record<string, any> = {}
    if (policy) params.policy = JSON.stringify(policy)

    const response = await this.client.get<ConversationContext>(
      `/v1/context/${branchId}`,
      { params }
    )
    return response.data
  }

  // Health
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health')
    return response.data
  }
}

export const api = new ConvoHubAPI()
