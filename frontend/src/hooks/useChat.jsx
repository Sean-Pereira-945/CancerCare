import { useState, useCallback } from 'react'
import { chatAPI } from '../lib/api'

export function useChat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m CancerCare AI. I can answer questions about your reports, treatment, diet, symptoms, and more. How can I help you today? 💙'
    }
  ])
  const [loading, setLoading] = useState(false)

  const sendMessage = useCallback(async (input) => {
    if (!input.trim() || loading) return

    const userMsg = { role: 'user', content: input }
    const history = messages.slice(-6)
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const { data } = await chatAPI.sendMessage(input, history)
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I\'m sorry, I encountered an error. Please check that the backend is running and try again.'
      }])
    } finally {
      setLoading(false)
    }
  }, [messages, loading])

  const clearChat = useCallback(() => {
    setMessages([{
      role: 'assistant',
      content: 'Chat cleared. How can I help you? 💙'
    }])
  }, [])

  return { messages, loading, sendMessage, clearChat }
}

export default useChat
