import React, { useCallback, useMemo, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import MessageNode from './MessageNode'
import { FlowNode, FlowEdge } from '@/types/flow'
import { Branch, Message } from '@/types/api'

interface ConversationFlowProps {
  branches: Branch[]
  messages: Record<string, Message[]>
  onSendMessage: (branchId: string, text: string) => void
  onCreateBranch: (fromBranchId: string) => void
  onNodeSelect: (nodeId: string) => void
  selectedNodeId: string | null
}

// Define nodeTypes at module scope to avoid re-creation warnings
const nodeTypes: NodeTypes = {
  messageNode: MessageNode,
}

export default function ConversationFlow({
  branches,
  messages,
  onSendMessage,
  onCreateBranch,
  onNodeSelect,
  selectedNodeId,
}: ConversationFlowProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Convert branches to flow nodes
  const flowNodes = useMemo(() => {
    return branches.map((branch, index) => {
      const branchMessages = messages[branch.id] || []
      const lastMessage = branchMessages[branchMessages.length - 1]
      
      // Determine role based on last message or branch type
      let role: 'user' | 'assistant' | 'system' | 'merge' = 'user'
      if (lastMessage) {
        role = lastMessage.role
      } else if (branch.name.toLowerCase().includes('merge')) {
        role = 'merge'
      }

      // Determine title
      let title = branch.name
      if (lastMessage) {
        const content = typeof lastMessage.content === 'string' 
          ? lastMessage.content 
          : lastMessage.content?.text || ''
        title = content.substring(0, 20) + (content.length > 20 ? '...' : '')
      }

      return {
        id: branch.id,
        type: 'messageNode' as const,
        position: {
          x: 250 + (index % 3) * 300,
          y: 100 + Math.floor(index / 3) * 200,
        },
        data: {
          branch,
          messages: branchMessages,
          role,
          title,
          content: lastMessage?.content || '',
          onSendMessage: (text: string) => onSendMessage(branch.id, text),
          onCreateBranch: () => onCreateBranch(branch.id),
        },
        selected: selectedNodeId === branch.id,
      } as Node
    })
  }, [branches, messages, selectedNodeId])

  // Create edges based on branch relationships
  const flowEdges = useMemo(() => {
    const edges: Edge[] = []
    
    branches.forEach((branch) => {
      if (branch.created_from_branch_id) {
        edges.push({
          id: `${branch.created_from_branch_id}-${branch.id}`,
          source: branch.created_from_branch_id,
          target: branch.id,
          type: 'smoothstep',
          data: {
            type: 'parent',
          },
        })
      }
    })
    
    return edges
  }, [branches])

  // Update nodes and edges when data changes
  React.useEffect(() => {
    setNodes(flowNodes)
  }, [flowNodes, setNodes])

  React.useEffect(() => {
    setEdges(flowEdges)
  }, [flowEdges, setEdges])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      onNodeSelect(node.id)
    },
    [onNodeSelect]
  )

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-background"
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as any
            switch (data?.role) {
              case 'system':
                return '#3b82f6'
              case 'user':
                return '#10b981'
              case 'assistant':
                return '#8b5cf6'
              case 'merge':
                return '#f59e0b'
              default:
                return '#6b7280'
            }
          }}
        />
      </ReactFlow>
    </div>
  )
}
