import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

export function formatDate(dateString: string): string {
  // Use a consistent date format that doesn't change between server and client
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export function getNodeColor(role: string): string {
  switch (role) {
    case 'system':
      return 'bg-blue-500'
    case 'user':
      return 'bg-green-500'
    case 'assistant':
      return 'bg-purple-500'
    case 'merge':
      return 'bg-amber-500'
    default:
      return 'bg-gray-500'
  }
}

export function getNodeBorderColor(role: string): string {
  switch (role) {
    case 'system':
      return 'border-blue-500'
    case 'user':
      return 'border-green-500'
    case 'assistant':
      return 'border-purple-500'
    case 'merge':
      return 'border-amber-500'
    default:
      return 'border-gray-500'
  }
}
