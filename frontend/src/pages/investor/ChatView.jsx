import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth.js';
import { useSSE } from '../../hooks/useSSE.js';
import { useChatHistory } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import ConfidenceBadge from '../../components/ConfidenceBadge.jsx';

const SUGGESTED_QUERIES = [
  'What is my current XIRR and how does it compare to Nifty 50?',
  'Am I on track for retirement?',
  'Should I switch to old or new tax regime?',
  'How much more should I invest to reach my education goal?',
];

export default function ChatView() {
  const { clientId } = useAuth();
  const { data: historyData } = useChatHistory(clientId);
  const { fullText, isStreaming, isDone, error: streamError, toolCalls, confidence, sendMessage, reset } = useSSE();

  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const bottomRef = useRef(null);

  // Load history on mount
  useEffect(() => {
    if (historyData?.data) {
      setMessages(historyData.data.map((m) => ({
        role: m.role,
        content: m.content,
        confidence: m.confidence,
      })));
    }
  }, [historyData]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, fullText]);

  async function handleSend(e) {
    e?.preventDefault();
    if (!query.trim() || isStreaming) return;

    const userMsg = { role: 'user', content: query.trim() };
    setMessages((prev) => [...prev, userMsg]);
    const q = query.trim();
    setQuery('');
    reset();

    await sendMessage({ client_id: clientId, query: q });
  }

  // When stream completes, add assistant message
  useEffect(() => {
    if (isDone && fullText) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: fullText, confidence },
      ]);
      reset();
    }
  }, [isDone]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-bold text-gray-900">AI Financial Advisor</h1>
        <p className="text-xs text-gray-500 mt-0.5">Powered by Claude · SEBI Registered</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="py-8">
            <p className="text-center text-gray-400 mb-6">Ask me anything about your finances</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTED_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => { setQuery(q); }}
                  className="text-left px-4 py-3 rounded-xl border border-gray-200 text-sm text-gray-600 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}

        {/* Streaming in-progress */}
        {isStreaming && fullText && (
          <MessageBubble message={{ role: 'assistant', content: fullText }} streaming />
        )}
        {isStreaming && !fullText && toolCalls.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <LoadingSpinner size="sm" />
            <span>Thinking...</span>
          </div>
        )}
        {toolCalls.length > 0 && isStreaming && (
          <div className="text-xs text-blue-600 bg-blue-50 rounded-lg px-3 py-2">
            Using tool: {toolCalls[toolCalls.length - 1].name}...
          </div>
        )}

        {streamError && (
          <div className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{streamError}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="px-6 py-4 border-t border-gray-200 bg-white">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your portfolio, goals, or tax..."
            className="input-field flex-1"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !query.trim()}
            className="btn-primary px-6"
          >
            {isStreaming ? '...' : 'Send'}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          AI responses are for informational purposes only. Not financial advice. SEBI disclaimer applies.
        </p>
      </form>
    </div>
  );
}

function MessageBubble({ message, streaming }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'}`}>
        <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
        {!isUser && message.confidence != null && (
          <div className="mt-2">
            <ConfidenceBadge score={message.confidence} />
          </div>
        )}
        {streaming && <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse ml-1 align-middle" />}
      </div>
    </div>
  );
}
