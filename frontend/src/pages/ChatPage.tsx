import { useState } from 'react'

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { id: '1', role: 'assistant', content: 'Hello! How can I help you with your documents today?' },
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return

    const newMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    }

    setMessages([...messages, newMessage])
    setInput('')

    // TODO: Send to API
  }

  return (
    <div className="container" style={{ maxWidth: '800px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <h1 style={{ marginBottom: '20px' }}>Chat</h1>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '20px',
          marginBottom: '20px',
          background: '#f9f9f9',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              marginBottom: '15px',
              textAlign: msg.role === 'user' ? 'right' : 'left',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                maxWidth: '70%',
                padding: '12px 15px',
                borderRadius: '8px',
                background: msg.role === 'user' ? '#007bff' : '#e9ecef',
                color: msg.role === 'user' ? 'white' : '#333',
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          style={{ flex: 1 }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          style={{
            background: '#007bff',
            color: 'white',
            padding: '10px 20px',
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
