'use client'

import React, { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import ConversationFlow from '@/components/flow/ConversationFlow'
import InspectorPanel from '@/components/flow/InspectorPanel'
import { Branch, Message } from '@/types/api'
import { generateId } from '@/lib/utils'

// Use a consistent date for demo data to avoid hydration issues
const DEMO_DATE = '2024-01-15T10:30:00.000Z'

export default function Home() {
  // Simple state for testing
  const [branches, setBranches] = useState<Branch[]>([
    {
      id: 'branch-1',
      thread_id: 'thread-1',
      name: 'Main Branch',
      description: 'Main research branch',
      is_active: true,
      created_at: DEMO_DATE,
      updated_at: DEMO_DATE,
    },
    {
      id: 'branch-2',
      thread_id: 'thread-1',
      name: 'Research Branch',
      description: 'Research findings',
      created_from_branch_id: 'branch-1',
      is_active: true,
      created_at: DEMO_DATE,
      updated_at: DEMO_DATE,
    },
  ])

  const [messages, setMessages] = useState<Record<string, Message[]>>({
    'branch-1': [
      {
        id: 'msg-1',
        branch_id: 'branch-1',
        role: 'user',
        content: { text: 'What are the main challenges in AI safety?' },
        created_at: DEMO_DATE,
        updated_at: DEMO_DATE,
      },
      {
        id: 'msg-2',
        branch_id: 'branch-1',
        role: 'assistant',
        content: { text: 'AI safety challenges include alignment, control, and value specification.' },
        created_at: DEMO_DATE,
        updated_at: DEMO_DATE,
      },
    ],
    'branch-2': [
      {
        id: 'msg-3',
        branch_id: 'branch-2',
        role: 'user',
        content: { text: 'Focus on technical alignment issues' },
        created_at: DEMO_DATE,
        updated_at: DEMO_DATE,
      },
    ],
  })

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>('branch-1')
  const [selectedBranches, setSelectedBranches] = useState<string[]>([])

  // Mock handlers
  const handleSendMessage = useCallback((branchId: string, text: string) => {
    console.log('Sending message:', text, 'to branch:', branchId)
    const newMessage: Message = {
      id: `msg-${generateId()}`,
      branch_id: branchId,
      role: 'user',
      content: { text },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    
    setMessages(prev => ({
      ...prev,
      [branchId]: [...(prev[branchId] || []), newMessage],
    }))
  }, [])

  const handleCreateBranch = useCallback((fromBranchId: string) => {
    console.log('Creating branch from:', fromBranchId)
    const newBranch: Branch = {
      id: `branch-${generateId()}`,
      thread_id: 'thread-1',
      name: `Branch ${branches.length + 1}`,
      description: 'New branch',
      created_from_branch_id: fromBranchId,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    
    setBranches(prev => [...prev, newBranch])
    setSelectedNodeId(newBranch.id)
  }, [branches.length])

  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId)
    
    // Handle multi-selection for diff
    if (selectedBranches.includes(nodeId)) {
      setSelectedBranches(selectedBranches.filter((id) => id !== nodeId))
    } else if (selectedBranches.length < 2) {
      setSelectedBranches([...selectedBranches, nodeId])
    } else {
      setSelectedBranches([selectedBranches[1], nodeId])
    }
  }, [selectedBranches])

  const handleMergeBranches = useCallback((sourceBranchId: string, targetBranchId: string) => {
    console.log('Merging branches:', sourceBranchId, 'into', targetBranchId)
    setSelectedBranches([])
  }, [])

  // Get data for selected branch
  const selectedBranch = branches.find((b) => b.id === selectedNodeId) || null
  const selectedBranchMessages = messages[selectedNodeId || ''] || []

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
            <span className="text-sm text-muted-foreground">
              Demo Mode
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => console.log('New thread')}
            >
              New Thread
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex">
        {/* Left pane - Flow */}
        <div className="flex-1 relative">
          <ConversationFlow
            branches={branches}
            messages={messages}
            onSendMessage={handleSendMessage}
            onCreateBranch={handleCreateBranch}
            onNodeSelect={handleNodeSelect}
            selectedNodeId={selectedNodeId}
          />
        </div>

        {/* Right pane - Inspector */}
        <div className="w-1/3 border-l bg-background">
          <InspectorPanel
            selectedBranch={selectedBranch}
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
