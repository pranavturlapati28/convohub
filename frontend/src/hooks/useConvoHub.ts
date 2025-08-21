import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import {
  LoginRequest,
  CreateThreadRequest,
  CreateBranchRequest,
  SendMessageRequest,
  MergeRequest,
} from '@/types/api'

// Query keys
export const queryKeys = {
  threads: ['threads'] as const,
  thread: (id: string) => ['threads', id] as const,
  branches: (threadId: string) => ['threads', threadId, 'branches'] as const,
  messages: (branchId: string) => ['branches', branchId, 'messages'] as const,
  summaries: (threadId: string) => ['threads', threadId, 'summaries'] as const,
  memories: (threadId: string) => ['threads', threadId, 'memories'] as const,
  context: (branchId: string) => ['branches', branchId, 'context'] as const,
  diff: (leftBranchId: string, rightBranchId: string, mode: string) =>
    ['diff', leftBranchId, rightBranchId, mode] as const,
}

// Authentication
export function useLogin() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: LoginRequest) => api.login(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.threads })
    },
  })
}

// Threads
export function useCreateThread() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: CreateThreadRequest) => api.createThread(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.threads })
    },
  })
}

export function useThreadSummaries(threadId: string) {
  return useQuery({
    queryKey: queryKeys.summaries(threadId),
    queryFn: () => api.getThreadSummaries(threadId),
    enabled: !!threadId,
  })
}

export function useThreadMemories(threadId: string) {
  return useQuery({
    queryKey: queryKeys.memories(threadId),
    queryFn: () => api.getThreadMemories(threadId),
    enabled: !!threadId,
  })
}

// Branches
export function useCreateBranch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ threadId, request }: { threadId: string; request: CreateBranchRequest }) =>
      api.createBranch(threadId, request),
    onSuccess: (_, { threadId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.branches(threadId) })
    },
  })
}

// Messages
export function useSendMessage() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({
      branchId,
      request,
      idempotencyKey,
    }: {
      branchId: string
      request: SendMessageRequest
      idempotencyKey?: string
    }) => api.sendMessage(branchId, request, idempotencyKey),
    onSuccess: (_, { branchId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.messages(branchId) })
    },
  })
}

export function useMessages(branchId: string, cursor?: string, limit: number = 50) {
  return useQuery({
    queryKey: [...queryKeys.messages(branchId), cursor, limit],
    queryFn: () => api.listMessages(branchId, cursor, limit),
    enabled: !!branchId,
  })
}

// Merge
export function useMerge() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (request: MergeRequest) => api.merge(request),
    onSuccess: (_, request) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.messages(request.source_branch_id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.messages(request.target_branch_id) })
    },
  })
}

export function useMergeStrategies() {
  return useQuery({
    queryKey: ['merge-strategies'],
    queryFn: () => api.getMergeStrategies(),
  })
}

// Diff
export function useDiff(
  leftBranchId: string,
  rightBranchId: string,
  mode: 'summary' | 'messages' | 'memory' = 'messages'
) {
  return useQuery({
    queryKey: queryKeys.diff(leftBranchId, rightBranchId, mode),
    queryFn: () => api.diff(leftBranchId, rightBranchId, mode),
    enabled: !!leftBranchId && !!rightBranchId,
  })
}

export function useDiffMemory(leftBranchId: string, rightBranchId: string) {
  return useQuery({
    queryKey: queryKeys.diff(leftBranchId, rightBranchId, 'memory'),
    queryFn: () => api.diffMemory(leftBranchId, rightBranchId),
    enabled: !!leftBranchId && !!rightBranchId,
  })
}

export function useDiffSummary(leftBranchId: string, rightBranchId: string) {
  return useQuery({
    queryKey: queryKeys.diff(leftBranchId, rightBranchId, 'summary'),
    queryFn: () => api.diffSummary(leftBranchId, rightBranchId),
    enabled: !!leftBranchId && !!rightBranchId,
  })
}

export function useDiffMessages(leftBranchId: string, rightBranchId: string) {
  return useQuery({
    queryKey: queryKeys.diff(leftBranchId, rightBranchId, 'messages'),
    queryFn: () => api.diffMessages(leftBranchId, rightBranchId),
    enabled: !!leftBranchId && !!rightBranchId,
  })
}

// Context
export function useContext(branchId: string, policy?: any) {
  return useQuery({
    queryKey: [...queryKeys.context(branchId), policy],
    queryFn: () => api.getContext(branchId, policy),
    enabled: !!branchId,
  })
}

// Health
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
  })
}
