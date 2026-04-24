import { useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import ChatBubble from '../components/ChatBubble'
import MedicalDisclaimer from '../components/MedicalDisclaimer'

export default function Chatbot() {
  const { messages, loading, sendMessage, clearChat } = useChat()
  const inputRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const value = inputRef.current?.value?.trim()
    if (value) {
      sendMessage(value)
      inputRef.current.value = ''
    }
  }

  const suggestions = [
    'What are common side effects of chemotherapy?',
    'How can I manage fatigue during treatment?',
    'What foods should I eat during radiation therapy?',
    'Tell me about my latest report findings'
  ]

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] lg:h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 to-teal-500 px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">CancerCare AI Assistant</h1>
            <p className="text-teal-100 text-xs mt-0.5">Powered by your reports + medical knowledge base</p>
          </div>
          <button
            onClick={clearChat}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg backdrop-blur transition-colors"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="px-4 pt-3">
        <MedicalDisclaimer />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length <= 1 && (
          <div className="mt-8 mb-4">
            <p className="text-gray-400 text-xs text-center mb-4">Quick suggestions:</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl mx-auto">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { inputRef.current.value = s; handleSend() }}
                  className="text-left px-4 py-3 bg-white border border-gray-100 rounded-xl text-sm text-gray-600 hover:border-teal-300 hover:bg-teal-50 transition-all duration-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} index={i} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center text-white text-xs font-bold mr-2">
              AI
            </div>
            <div className="bg-white border border-gray-100 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-soft" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-soft" style={{ animationDelay: '200ms' }} />
                <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-soft" style={{ animationDelay: '400ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 bg-white px-4 py-3">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <input
            ref={inputRef}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your treatment, diet, symptoms..."
            className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 focus:bg-white transition-all"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="px-5 py-2.5 btn-primary text-sm font-medium disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
