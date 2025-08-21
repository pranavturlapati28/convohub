import React, { useState, useCallback } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import { cn, getNodeColor, getNodeBorderColor, truncateText } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FlowNode } from '@/types/flow'

interface MessageNodeProps extends NodeProps<FlowNode['data']> {
  // Remove custom props that aren't supported by React Flow
}

export default function MessageNode({
  data,
  selected,
}: MessageNodeProps) {
  const [showInput, setShowInput] = useState(false)
  const [messageText, setMessageText] = useState('')

  const handleSendMessage = useCallback(() => {
    if (!messageText.trim()) return
    if (data.onSendMessage) {
      data.onSendMessage(messageText.trim())
    } else {
      console.log('Sending message:', messageText, 'to branch:', data.branch.id)
    }
    setMessageText('')
    setShowInput(false)
  }, [messageText, data])

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSendMessage()
      }
    },
    [handleSendMessage]
  )

  const handleCreateBranch = useCallback(() => {
    if (data.onCreateBranch) {
      data.onCreateBranch()
    } else {
      console.log('Creating branch from:', data.branch.id)
    }
  }, [data])

  const getRoleIcon = () => {
    switch (data.role) {
      case 'system':
        return '⚙️'
      case 'user':
        return '👤'
      case 'assistant':
        return '🤖'
      case 'merge':
        return '🔄'
      default:
        return '💬'
    }
  }

  const getLastMessageContent = () => {
    if (data.messages.length === 0) return 'No messages'
    const lastMessage = data.messages[data.messages.length - 1]
    return truncateText(
      typeof lastMessage.content === 'string'
        ? lastMessage.content
        : lastMessage.content?.text || 'No text content',
      30
    )
  }

  return (
    <div
      className={cn(
        'relative min-w-[200px] rounded-lg border-2 bg-background p-3 shadow-lg transition-all',
        getNodeBorderColor(data.role),
        selected && 'ring-2 ring-primary ring-offset-2'
      )}
    >
      {/* Input handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-primary border-2 border-background"
      />

      {/* Node content */}
      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getRoleIcon()}</span>
            <div>
              <h3 className="text-sm font-medium text-foreground">
                {data.title}
              </h3>
              <p className="text-xs text-muted-foreground">
                {data.messages.length} messages
              </p>
            </div>
          </div>
          
          {/* Action buttons */}
          <div className="flex space-x-1">
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6"
              onClick={() => setShowInput(!showInput)}
              title="Send message"
            >
              💬
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6"
              onClick={handleCreateBranch}
              title="Create branch"
            >
              ➕
            </Button>
          </div>
        </div>

        {/* Last message preview */}
        <div className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
          {getLastMessageContent()}
        </div>

        {/* Message input */}
        {showInput && (
          <div className="space-y-2">
            <Input
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="h-8 text-xs"
            />
            <div className="flex justify-end">
              <Button
                size="sm"
                onClick={handleSendMessage}
                disabled={!messageText.trim()}
                className="h-6 px-2 text-xs"
              >
                📤 Send
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Output handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-primary border-2 border-background"
      />
    </div>
  )
}
