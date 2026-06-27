'use client';

import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { Send, Plus, Sparkles, Command, Zap, Brain, FileText, Users, ArrowRight } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    // Guarantees scroll happens after DOM paints the new message
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, [messages]);

  const sendMessage = async (overrideText = null) => {
    const question = overrideText || input.trim();
    if (!question || isLoading) return;

    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    if (!overrideText) setInput('');
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'assistant', content: '', isLoading: true }]);

    try {
      const response = await fetch(`${API_URL}/api/v1/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, conversation_id: conversationId }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);
      const data = await response.json();

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          confidence: data.confidence,
          reasoning_trace: data.reasoning_trace,
          requires_clarification: data.requires_clarification,
          clarification_question: data.clarification_question,
        };
        return updated;
      });
      setConversationId(data.conversation_id);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'System error. Please ensure Ollama is running locally.',
          isError: true,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const submitFeedback = async (messageIndex, rating) => {
    const msg = messages[messageIndex];
    if (!msg || msg.role !== 'assistant') return;
    try {
      await fetch(`${API_URL}/api/v1/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId || 'unknown',
          question: messages[messageIndex - 1]?.content || '',
          answer: msg.content, rating,
        }),
      });
      setMessages((prev) => {
        const updated = [...prev];
        updated[messageIndex] = { ...updated[messageIndex], feedback: rating };
        return updated;
      });
    } catch (error) { console.error('Feedback error:', error); }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const suggestedQueries = [
    { icon: <FileText size={20} />, text: "What is the remote work policy?", desc: "HR & Policies" },
    { icon: <Zap size={20} />, text: "How do I deploy to production?", desc: "Engineering & DevOps" },
    { icon: <Users size={20} />, text: "What is the employee leave policy?", desc: "Work from Home" },
    { icon: <Brain size={20} />, text: "How do I request a refund?", desc: "Customer Support" },
  ];

  const isEmpty = messages.length === 0;

  return (
    // Root container: Fixed full viewport height
    <div className="h-screen flex flex-col bg-[#0a0a0a] overflow-hidden">
      
      {/* Background orbs - Fixed behind everything */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] rounded-full bg-gradient-to-br from-indigo-600/20 via-purple-600/10 to-transparent blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-[-30%] right-[-10%] w-[60%] h-[60%] rounded-full bg-gradient-to-tl from-cyan-600/20 via-blue-600/10 to-transparent blur-3xl animate-pulse-slow-delayed" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-cyan-500/5 blur-3xl" />
        <div className="absolute inset-0 opacity-[0.03]" style={{ 
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }} />
      </div>

      {/* 1. Header - Pinned at top, never scrolls */}
      <header className="relative z-20 flex-shrink-0 flex items-center justify-between px-8 py-4 border-b border-white/5 bg-black/60 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-[0_0_30px_rgba(99,102,241,0.3)]">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Enterprise Knowledge Agent
            </h1>
            <p className="text-[10px] text-gray-500 font-medium tracking-[0.2em] uppercase">
              Autonomous RAG · Llama 3.2 3B
            </p>
          </div>
        </div>
        <button 
          onClick={startNewChat}
          className="flex items-center gap-2 text-xs font-semibold text-gray-300 hover:text-white px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all duration-300 shadow-sm hover:shadow-indigo-500/10"
        >
          <Plus size={15} /> New Session
        </button>
      </header>

      {/* 2. Scrollable Content Area - flex-1 takes remaining space, overflow-y-auto allows scroll */}
      <main ref={scrollContainerRef} className="relative z-10 flex-1 overflow-y-auto">
        {isEmpty ? (
          // Hero - Centered Layout
          <div className="min-h-full flex flex-col items-center justify-center px-8 py-12 text-center">
            <div className="max-w-3xl mx-auto animate-fade-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold tracking-wider mb-8">
                <Sparkles size={14} /> AI-Powered Knowledge
              </div>
              <h1 className="text-6xl md:text-7xl font-extrabold leading-[1.05] tracking-tight mb-6">
                Ask your
                <br />
                <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                  Enterprise Data
                </span>
              </h1>
              <p className="text-gray-400 text-lg max-w-2xl mx-auto mb-12 leading-relaxed">
                The agent searches, reasons, and cites sources – all powered by local Llama 3.2.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
                {suggestedQueries.map((query, idx) => (
                  <button
                    key={idx}
                    onClick={() => { setInput(query.text); sendMessage(query.text); }}
                    className="group flex items-center gap-4 p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 hover:border-white/20 transition-all duration-300 shadow-lg hover:shadow-indigo-500/10 text-left"
                  >
                    <div className="w-11 h-11 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/20 group-hover:text-indigo-300 transition-colors flex-shrink-0">
                      {query.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-200 group-hover:text-white transition-colors truncate">
                        {query.text}
                      </p>
                      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">
                        {query.desc}
                      </p>
                    </div>
                    <ArrowRight size={16} className="text-gray-600 group-hover:text-indigo-400 transition-colors flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Messages - Padded so content isn't hidden behind header/footer
          <div className="max-w-5xl w-full mx-auto px-8 py-8 space-y-6">
            {messages.map((msg, idx) => (
              <MessageBubble 
                key={idx} 
                message={msg} 
                onFeedback={(rating) => submitFeedback(idx, rating)}
              />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </main>

      {/* 3. Footer Input Bar - Pinned at bottom, never scrolls */}
      <footer className="relative z-20 flex-shrink-0 pb-6 pt-4 px-8 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a] to-transparent">
        <div className="max-w-4xl mx-auto">
          <form 
            onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
            className={`relative flex items-center bg-white/5 backdrop-blur-xl rounded-2xl border transition-all duration-300 shadow-2xl ${
              isFocused 
                ? 'border-indigo-500/50 shadow-indigo-500/20' 
                : 'border-white/10 hover:border-white/20'
            }`}
          >
            <div className="pl-5 pr-2 text-gray-500">
              <Command size={18} />
            </div>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask the agent a question..."
              className="flex-1 bg-transparent py-4 pr-14 text-[15px] font-medium text-gray-200 placeholder-gray-500 focus:outline-none"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`absolute right-2.5 p-2.5 rounded-xl transition-all duration-200 ${
                input.trim() && !isLoading
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:scale-105' 
                  : 'bg-white/5 text-gray-600 cursor-not-allowed'
              }`}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </footer>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes pulse-slow {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.1); opacity: 0.9; }
        }
        @keyframes pulse-slow-delayed {
          0%, 100% { transform: scale(1); opacity: 0.4; }
          50% { transform: scale(1.15); opacity: 0.7; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 10s ease-in-out infinite;
        }
        .animate-pulse-slow-delayed {
          animation: pulse-slow-delayed 12s ease-in-out infinite;
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
    </div>
  );
}