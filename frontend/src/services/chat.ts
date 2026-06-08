import apiClient from './api'

interface MessageSource {
  document_id: string
  source: string
  chunk_index?: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: MessageSource[]
  created_at: string
}

interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  messages?: Message[]
}

interface ChatResponse {
  conversation_id: string
  response: string
  sources: MessageSource[]
}

export const chatService = {
  listConversations: async (): Promise<Conversation[]> => {
    const response = await apiClient.get('/api/v1/chat/conversations')
    return response.data
  },

  createConversation: async (title?: string): Promise<Conversation> => {
    const response = await apiClient.post('/api/v1/chat/conversations', {
      title: title || undefined,
    })
    return response.data
  },

  getConversation: async (conversationId: string): Promise<Conversation> => {
    const response = await apiClient.get(
      `/api/v1/chat/conversations/${conversationId}`
    )
    return response.data
  },

  sendMessage: async (
    conversationId: string,
    message: string
  ): Promise<ChatResponse> => {
    const response = await apiClient.post(
      `/api/v1/chat/conversations/${conversationId}/messages`,
      { content: message }
    )
    return response.data
  },

  deleteConversation: async (conversationId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/chat/conversations/${conversationId}`)
  },
}
