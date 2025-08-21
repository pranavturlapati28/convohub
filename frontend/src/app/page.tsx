"use client"

import React, { useMemo, useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ConversationFlow from '@/components/flow/ConversationFlow'
import InspectorPanel from '@/components/flow/InspectorPanel'
import { Branch, Message, SendMessageRequest } from '@/types/api'
import { useBranches, useCreateBranch, useMessages, useSendMessage, useMerge, useLogin, useCreateThread, useThreads } from '@/hooks/useConvoHub'
import { useSSE } from '@/hooks/useSSE'

// TEMP: choose a thread to work with (replace with real selection/auth later)
const DEFAULT_THREAD_ID = process.env.NEXT_PUBLIC_CONVOHUB_THREAD_ID || ''
const DEV_EMAIL = process.env.NEXT_PUBLIC_CONVOHUB_DEV_EMAIL
const DEV_TENANT = process.env.NEXT_PUBLIC_CONVOHUB_DEV_TENANT
const DEV_PASSWORD = process.env.NEXT_PUBLIC_CONVOHUB_DEV_PASSWORD

export default function Home() {
  // Auto-login in dev if creds provided
  const login = useLogin()
  React.useEffect(() => {
    if (DEV_EMAIL && DEV_TENANT && DEV_PASSWORD) {
      login.mutate({ email: DEV_EMAIL, tenant_domain: DEV_TENANT, password: DEV_PASSWORD })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedBranches, setSelectedBranches] = useState<string[]>([])
  const [threadId, setThreadId] = useState<string>(DEFAULT_THREAD_ID)
  const [authed, setAuthed] = useState<boolean>(typeof window !== 'undefined' && !!window.localStorage.getItem('convohub_token'))

  React.useEffect(() => {
    const token = typeof window !== 'undefined' ? window.localStorage.getItem('convohub_token') : null
    setAuthed(!!token)
  }, [login.isSuccess])

  // Live data
  const { data: threads = [] } = useThreads()
  const { data: branches = [] } = useBranches(threadId)

  const selectedBranch = useMemo<Branch | null>(() => {
    if (!selectedNodeId) return branches[0] ?? null
    return branches.find((b) => b.id === selectedNodeId) ?? null
  }, [branches, selectedNodeId])

  const { data: messagesResp } = useMessages(selectedBranch?.id || '')
  const selectedBranchMessages: Message[] = messagesResp?.messages ?? []

  // Mutations
  const createBranch = useCreateBranch()
  const createThread = useCreateThread()
  const sendMessage = useSendMessage()
  const mergeMut = useMerge()

  // SSE live updates using same base URL
  const base = (process.env.NEXT_PUBLIC_CONVOHUB_API_URL as string) || 'http://127.0.0.1:8000'
  useSSE(`${base}/v1/events`, true)

  const handleSendMessage = useCallback((branchId: string, text: string) => {
    const payload: SendMessageRequest = { role: 'user', text }
    sendMessage.mutate({ branchId, request: payload })
  }, [sendMessage])

  const handleCreateBranch = useCallback((fromBranchId: string) => {
    if (!threadId) return
    const request = { name: 'New Branch', description: 'Created from UI', created_from_branch_id: fromBranchId }
    createBranch.mutate({ threadId, request })
  }, [createBranch, threadId])

  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId)
    setSelectedBranches((prev) => {
      if (prev.includes(nodeId)) return prev.filter((id) => id !== nodeId)
      if (prev.length < 2) return [...prev, nodeId]
      return [prev[1], nodeId]
    })
  }, [])

  const handleMergeBranches = useCallback((sourceBranchId: string, targetBranchId: string) => {
    if (!threadId) return
    mergeMut.mutate({ thread_id: threadId, source_branch_id: sourceBranchId, target_branch_id: targetBranchId, strategy: 'append-last' })
    setSelectedBranches([])
  }, [mergeMut, threadId])

  if (!authed) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="w-full max-w-sm space-y-3 p-6 border rounded-lg">
          <h2 className="text-lg font-semibold">Sign in</h2>
          <Input placeholder="Email" defaultValue={DEV_EMAIL || ''} onBlur={(e) => (window as any)._email = e.target.value} />
          <Input placeholder="Tenant domain" defaultValue={DEV_TENANT || ''} onBlur={(e) => (window as any)._tenant = e.target.value} />
          <Input placeholder="Password" type="password" defaultValue={DEV_PASSWORD || ''} onBlur={(e) => (window as any)._password = e.target.value} />
          <Button
            onClick={() => login.mutate({
              email: ((window as any)._email || DEV_EMAIL || '').trim(),
              tenant_domain: ((window as any)._tenant || DEV_TENANT || '').trim(),
              password: ((window as any)._password || DEV_PASSWORD || '').trim(),
            })}
            disabled={login.isPending}
          >
            {login.isPending ? 'Signing in...' : 'Sign in'}
          </Button>
          {login.isError && <p className="text-sm text-red-500">Login failed</p>}
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-lg font-semibold">ConvoHub</h1>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs text-muted-foreground">Live</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <select
                value={threadId}
                onChange={(e) => setThreadId(e.target.value)}
                className="h-8 px-2 border rounded text-sm"
              >
                <option value="">Select Thread</option>
                {threads.map((thread) => (
                  <option key={thread.id} value={thread.id}>
                    {thread.title}
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => createThread.mutate({ title: 'New Thread' }, {
                  onSuccess: (thread) => setThreadId(thread.id),
                })}
                disabled={createThread.isPending}
              >
                {createThread.isPending ? 'Creating...' : 'New Thread'}
              </Button>
              {threadId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => createBranch.mutate({ threadId, request: { name: 'Root Branch' } })}
                  disabled={createBranch.isPending}
                >
                  {createBranch.isPending ? 'Creating...' : 'New Branch'}
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Left pane - Flow */}
        <div className="flex-1 relative">
          <ConversationFlow
            branches={branches}
            messages={{ [selectedBranch?.id || '']: selectedBranchMessages }}
            onSendMessage={handleSendMessage}
            onCreateBranch={handleCreateBranch}
            onNodeSelect={handleNodeSelect}
            selectedNodeId={selectedBranch?.id || null}
          />
        </div>

        {/* Right pane - Inspector */}
        <div className="w-1/3 border-l bg-background">
          <InspectorPanel
            selectedBranch={selectedBranch || null}
            messages={selectedBranchMessages}
            summaries={[]}
            memories={[]}
            diffResult={null}
            onMergeBranches={handleMergeBranches}
            selectedBranches={selectedBranches}
          />
        </div>
      </div>
    </div>
  )
}
