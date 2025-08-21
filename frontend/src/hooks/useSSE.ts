import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { queryKeys } from './useConvoHub'

interface SSEEvent {
  type: string
  data: any
}

export function useSSE(url: string, enabled: boolean = true) {
  const eventSourceRef = useRef<EventSource | null>(null)
  const queryClient = useQueryClient()

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: SSEEvent = JSON.parse(event.data)
        
        // Handle different event types
        switch (data.type) {
          case 'message_created':
            // Invalidate messages for the specific branch
            queryClient.invalidateQueries({
              queryKey: queryKeys.messages(data.data.branch_id),
            })
            break
            
          case 'branch_created':
            // Invalidate branches for the thread
            queryClient.invalidateQueries({
              queryKey: queryKeys.branches(data.data.thread_id),
            })
            break
            
          case 'merge_completed':
            // Invalidate messages for both branches
            queryClient.invalidateQueries({
              queryKey: queryKeys.messages(data.data.source_branch_id),
            })
            queryClient.invalidateQueries({
              queryKey: queryKeys.messages(data.data.target_branch_id),
            })
            break
            
          case 'summary_updated':
            // Invalidate summaries for the thread
            queryClient.invalidateQueries({
              queryKey: queryKeys.summaries(data.data.thread_id),
            })
            break
            
          case 'memory_updated':
            // Invalidate memories for the thread
            queryClient.invalidateQueries({
              queryKey: queryKeys.memories(data.data.thread_id),
            })
            break
            
          default:
            console.log('Unknown SSE event type:', data.type)
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error)
      }
    },
    [queryClient]
  )

  const handleError = useCallback((error: Event) => {
    console.error('SSE connection error:', error)
    // Attempt to reconnect after a delay
    setTimeout(() => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }, 5000)
  }, [])

  const handleOpen = useCallback(() => {
    console.log('SSE connection established')
  }, [])

  useEffect(() => {
    if (!enabled || !url) return

    // Create EventSource
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    // Add event listeners
    eventSource.addEventListener('message', handleMessage)
    eventSource.addEventListener('error', handleError)
    eventSource.addEventListener('open', handleOpen)

    // Cleanup function
    return () => {
      eventSource.removeEventListener('message', handleMessage)
      eventSource.removeEventListener('error', handleError)
      eventSource.removeEventListener('open', handleOpen)
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [url, enabled, handleMessage, handleError, handleOpen])

  // Return connection status
  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  }
}
