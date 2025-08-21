import React from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/simple-tabs'
import { Button } from '@/components/ui/button'
import { cn, formatDate, truncateText } from '@/lib/utils'
import { Branch, Message as MessageType, DiffResponse } from '@/types/api'

interface InspectorPanelProps {
  selectedBranch: Branch | null
  messages: MessageType[]
  summaries: any[]
  memories: any[]
  diffResult: DiffResponse | null
  onMergeBranches: (sourceBranchId: string, targetBranchId: string) => void
  selectedBranches: string[]
}

export default function InspectorPanel({
  selectedBranch,
  messages,
  summaries,
  memories,
  diffResult,
  onMergeBranches,
  selectedBranches,
}: InspectorPanelProps) {
  if (!selectedBranch) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <p>Select a branch to view details</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">{selectedBranch.name}</h2>
        <p className="text-sm text-muted-foreground">
          {selectedBranch.description || 'No description'}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Created: {formatDate(selectedBranch.created_at || '')}
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="messages" className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="messages">
            Messages
          </TabsTrigger>
          <TabsTrigger value="summary">
            Summary
          </TabsTrigger>
          <TabsTrigger value="memory">
            Memory
          </TabsTrigger>
          <TabsTrigger value="diff">
            Diff
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-hidden">
          {/* Messages Tab */}
          <TabsContent value="messages" className="h-full p-4 space-y-4 overflow-y-auto">
            <div className="space-y-3">
              {messages.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No messages in this branch
                </p>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'p-3 rounded-lg border',
                      message.role === 'user'
                        ? 'bg-blue-500/10 border-blue-500/20'
                        : message.role === 'assistant'
                        ? 'bg-purple-500/10 border-purple-500/20'
                        : 'bg-gray-500/10 border-gray-500/20'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium uppercase text-muted-foreground">
                        {message.role}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(message.created_at || '')}
                      </span>
                    </div>
                    <p className="text-sm">
                      {typeof message.content === 'string'
                        ? message.content
                        : message.content?.text || 'No text content'}
                    </p>
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          {/* Summary Tab */}
          <TabsContent value="summary" className="h-full p-4 space-y-4 overflow-y-auto">
            <div className="space-y-3">
              {summaries.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No summaries available
                </p>
              ) : (
                summaries.map((summary) => (
                  <div key={summary.id} className="p-3 rounded-lg border bg-muted/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-muted-foreground">
                        Summary
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {summary.token_count} tokens
                      </span>
                    </div>
                    <p className="text-sm">{summary.content}</p>
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          {/* Memory Tab */}
          <TabsContent value="memory" className="h-full p-4 space-y-4 overflow-y-auto">
            <div className="space-y-3">
              {memories.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No memories available
                </p>
              ) : (
                memories.map((memory) => (
                  <div key={memory.id} className="p-3 rounded-lg border bg-muted/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-muted-foreground">
                        {memory.memory_type}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {memory.confidence}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-medium">{memory.key}</p>
                      <p className="text-sm">{memory.value}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </TabsContent>

          {/* Diff Tab */}
          <TabsContent value="diff" className="h-full p-4 space-y-4 overflow-y-auto">
            <div className="space-y-4">
              {selectedBranches.length === 2 && (
                <Button
                  onClick={() => onMergeBranches(selectedBranches[0], selectedBranches[1])}
                  className="w-full"
                >
                  Merge Selected Branches
                </Button>
              )}

              {diffResult ? (
                <div className="space-y-3">
                  <div className="p-3 rounded-lg border bg-muted/50">
                    <h4 className="text-sm font-medium mb-2">Diff Results</h4>
                    <div className="space-y-2 text-xs">
                      <p>Mode: {diffResult.mode}</p>
                      <p>LCA: {diffResult.lca ? 'Found' : 'Not found'}</p>
                      <p>Source Delta: {diffResult.src_delta.length} messages</p>
                      <p>Target Delta: {diffResult.tgt_delta.length} messages</p>
                    </div>
                  </div>

                  {diffResult.summary_diff && (
                    <div className="p-3 rounded-lg border bg-muted/50">
                      <h4 className="text-sm font-medium mb-2">Summary Diff</h4>
                      <div className="space-y-2 text-xs">
                        <p>Common: {diffResult.summary_diff.common_content.length} chars</p>
                        <p>Left Only: {diffResult.summary_diff.left_only.length} chars</p>
                        <p>Right Only: {diffResult.summary_diff.right_only.length} chars</p>
                      </div>
                    </div>
                  )}

                  {diffResult.memory_diff && (
                    <div className="p-3 rounded-lg border bg-muted/50">
                      <h4 className="text-sm font-medium mb-2">Memory Diff</h4>
                      <div className="space-y-2 text-xs">
                        <p>Added: {diffResult.memory_diff.added.length}</p>
                        <p>Removed: {diffResult.memory_diff.removed.length}</p>
                        <p>Modified: {diffResult.memory_diff.modified.length}</p>
                        <p>Conflicts: {diffResult.memory_diff.conflicts.length}</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  Select two branches to compare
                </p>
              )}
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </div>
  )
}
