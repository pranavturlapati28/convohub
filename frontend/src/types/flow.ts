import { Node, Edge } from 'reactflow'
import { Branch, Message } from './api'

export interface FlowNode extends Node {
  data: {
    branch: Branch
    messages: Message[]
    role: 'user' | 'assistant' | 'system' | 'merge'
    title: string
    content?: string
    isSelected?: boolean
    onSendMessage?: (text: string) => void
    onCreateBranch?: () => void
  }
}

export interface FlowEdge extends Edge {
  data?: {
    label?: string
    type?: 'parent' | 'merge'
  }
}

export interface NodeData {
  branch: Branch
  messages: Message[]
  role: 'user' | 'assistant' | 'system' | 'merge'
  title: string
  content?: string
  isSelected?: boolean
  onSendMessage?: (text: string) => void
  onCreateBranch?: () => void
}

export interface FlowState {
  nodes: FlowNode[]
  edges: FlowEdge[]
  selectedNodeId: string | null
  selectedBranchId: string | null
}
