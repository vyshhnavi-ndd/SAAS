import { useState, useEffect, useRef, useContext } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'
import { chatService } from '../services/chat'
import styles from './ChatPage.module.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: any[]
  created_at: string
}

interface Conversation {
  id: string
  title: string
  messages?: Message[]
}

export default function ChatPage() {
  const { user } = useContext(AuthContext)
  const [searchParams] = useSearchParams()
  const conversationId = searchParams.get('id')

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId)
    }
  }, [conversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const convs = await chatService.listConversations()
      setConversations(convs)
      if (convs.length > 0 && !conversationId) {
        setCurrentConversation(convs[0])
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load conversations')
    }
  }

  const loadConversation = async (convId: string) => {
    try {
      const conv = await chatService.getConversation(convId)
      setCurrentConversation(conv)
      setMessages(conv.messages || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load conversation')
    }
  }

  const handleNewConversation = async () => {
    try {
      const conv = await chatService.createConversation(
        `Chat ${new Date().toLocaleDateString()}`
      )
      setConversations([conv, ...conversations])
      setCurrentConversation(conv)
      setMessages([])
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create conversation')
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !currentConversation) return

    const userMessage = input
    setInput('')

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      sources: [],
      created_at: new Date().toISOString(),
    }
    setMessages([...messages, tempUserMsg])

    try {
      setLoading(true)
      const response = await chatService.sendMessage(
        currentConversation.id,
        userMessage
      )

      const assistantMsg: Message = {
        id: `temp-${Date.now()}-ai`,
        role: 'assistant',
        content: response.response,
        sources: response.sources || [],
        created_at: new Date().toISOString(),
      }

      setMessages((prev) => [...prev.slice(1), tempUserMsg, assistantMsg])
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message')
      // Remove temp message on error
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteConversation = async (convId: string) => {
    if (!window.confirm('Delete this conversation?')) return

    try {
      await chatService.deleteConversation(convId)
      setConversations(conversations.filter((c) => c.id !== convId))
      if (currentConversation?.id === convId) {
        setCurrentConversation(null)
        setMessages([])
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete conversation')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.sidebar}>
        <button onClick={handleNewConversation} className={styles.newChatBtn}>
          + New Chat
        </button>

        <div className={styles.conversationsList}>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`${styles.conversationItem} ${
                currentConversation?.id === conv.id ? styles.active : ''
              }`}
              onClick={() => setCurrentConversation(conv)}
            >
              <div className={styles.convTitle}>{conv.title}</div>
              <button
                className={styles.deleteConvBtn}
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteConversation(conv.id)
                }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.main}>
        {currentConversation ? (
          <>
            <div className={styles.header}>
              <h2>{currentConversation.title}</h2>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            <div className={styles.messagesContainer}>
              {messages.length === 0 ? (
                <div className={styles.emptyState}>
                  <p>Start a conversation</p>
                  <p className={styles.hint}>
                    Ask questions about your documents. The AI will search your files and provide answers with source citations.
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`${styles.message} ${styles[msg.role]}`}
                  >
                    <div className={styles.messageContent}>{msg.content}</div>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className={styles.sources}>
                        <p className={styles.sourcesLabel}>Sources:</p>
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className={styles.source}>
                            📄 {source.source}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}

              {loading && (
                <div className={styles.message + ' ' + styles.assistant}>
                  <div className={styles.typing}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className={styles.inputArea}>
              <div className={styles.inputWrapper}>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Ask a question about your documents..."
                  disabled={loading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || loading}
                  className={styles.sendBtn}
                >
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className={styles.noConversation}>
            <p>No conversation selected</p>
            <button onClick={handleNewConversation} className={styles.newChatBtn}>
              Create a new conversation
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

