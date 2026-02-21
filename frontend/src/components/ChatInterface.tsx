import { useState, useRef, useEffect } from "react"

type Message = {
  id: number
  role: "user" | "assistant"
  content: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = { id: Date.now(), role: "user", content: input }
    setMessages(prev => [...prev, userMessage])
    setInput("")
    setLoading(true)

    // TODO: replace with actual API call
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: "SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id;"
      }])
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-20">Ask anything about your database</p>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[70%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap
              ${msg.role === "user"
                ? "bg-blue-500 text-white rounded-br-sm"
                : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm"
              }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-2 text-gray-400 text-sm">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-3 flex gap-2 items-end">
        <textarea
          className="flex-1 resize-none bg-gray-100 rounded-xl px-4 py-2 text-sm outline-none max-h-40"
          rows={1}
          placeholder="Ask about your database..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              sendMessage()
            }
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-blue-500 hover:bg-blue-600 disabled:opacity-40 text-white px-4 py-2 rounded-xl text-sm"
        >
          Send
        </button>
      </div>

    </div>
  )
}
