import ReactMarkdown from 'react-markdown'

export default function ChatBubble({ message, index }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0 mt-1 shadow-md">
          AI
        </div>
      )}
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
          isUser
            ? 'bg-gradient-to-r from-teal-600 to-teal-500 text-white rounded-br-md'
            : 'bg-white border border-gray-100 text-gray-700 rounded-bl-md'
        }`}
      >
        <ReactMarkdown
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            code: ({ children }) => <code className="bg-gray-100 text-teal-700 px-1.5 py-0.5 rounded text-xs">{children}</code>,
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-600 to-gray-800 flex items-center justify-center text-white text-xs font-bold ml-2 flex-shrink-0 mt-1 shadow-md">
          You
        </div>
      )}
    </div>
  )
}
