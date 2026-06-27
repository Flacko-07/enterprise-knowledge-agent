'use client';

import { useState } from 'react';
import SourceCard from './SourceCard';
import { ThumbsUp, ThumbsDown, ChevronDown, HelpCircle, Search, Cpu, User, ShieldCheck, FileText } from 'lucide-react';

export default function MessageBubble({ message, onFeedback }) {
  const isUser = message.role === 'user';
  const isLoading = message.isLoading;
  const [showTrace, setShowTrace] = useState(false);

  // User Message: Clean, right-aligned, distinct gradient
  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in-up">
        <div className="max-w-2xl bg-gradient-to-br from-indigo-600/90 to-purple-700/90 rounded-2xl rounded-br-sm px-6 py-4 shadow-lg shadow-indigo-500/10">
          <p className="text-[15px] leading-relaxed text-white font-medium">{message.content}</p>
        </div>
      </div>
    );
  }

  // AI Message: Structured Card Layout
  return (
    <div className="flex gap-4 animate-fade-in-up">
      {/* Left Accent Line & Avatar */}
      <div className="flex flex-col items-center pt-5">
        <div className="w-10 h-10 rounded-xl bg-[var(--bg-card)] border border-[var(--border-medium)] flex items-center justify-center shadow-inner">
          <Cpu size={20} className="text-indigo-400" />
        </div>
      </div>

      {/* Main Content Card */}
      <div className="flex-1 min-w-0 bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl shadow-lg overflow-hidden">
        
        {/* Clarification UI */}
        {!isLoading && message.requires_clarification && (
          <div className="p-5 bg-amber-500/5 border-b border-amber-500/10">
            <div className="flex items-center gap-3">
              <HelpCircle size={18} className="text-amber-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-amber-400 mb-0.5">Clarification Needed</p>
                <p className="text-sm text-amber-200/70 leading-relaxed">{message.clarification_question}</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Answer Area */}
        <div className="p-6">
          {isLoading ? (
            <div className="flex gap-2 py-2 px-1">
              <span className="typing-dot w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
              <span className="typing-dot w-2.5 h-2.5 rounded-full bg-purple-400"></span>
              <span className="typing-dot w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
            </div>
          ) : (
            <div className={`prose-ai ${message.isError ? 'text-red-400' : ''}`}>
              {message.content}
            </div>
          )}
        </div>

        {/* Reasoning Trace - Sleek Accordion */}
        {!isLoading && message.reasoning_trace && message.reasoning_trace.length > 0 && (
          <div className="border-t border-[var(--border-subtle)]">
            <button 
              onClick={() => setShowTrace(!showTrace)}
              className="w-full flex items-center gap-2 px-6 py-3 text-xs font-semibold text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)] transition-colors"
            >
              <Cpu size={13} className="text-indigo-400" /> 
              <span>AGENT REASONING</span>
              <span className="ml-1 font-mono text-[10px] bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded">{message.reasoning_trace.length} steps</span>
              <ChevronDown size={14} className={`ml-auto transition-transform duration-200 ${showTrace ? 'rotate-180' : ''}`} />
            </button>
            {showTrace && (
              <div className="px-6 pb-4 pt-2 bg-[var(--bg-surface)]/50 border-t border-[var(--border-subtle)] animate-fade-in-up">
                <div className="space-y-3">
                  {message.reasoning_trace.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-xs">
                      <div className={`mt-0.5 p-1 rounded-md ${step.action === 'search_knowledge_base' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                        {step.action === 'search_knowledge_base' ? <Search size={12} /> : <HelpCircle size={12} />}
                      </div>
                      <div className="flex-1">
                        <span className="font-bold text-[var(--text-secondary)] uppercase tracking-wider text-[10px]">
                          {step.action === 'search_knowledge_base' ? 'Searched Database' : 'Asked User'}
                        </span>
                        <p className="text-[var(--text-primary)] mt-0.5 font-mono bg-[var(--bg-main)] px-2 py-1 rounded text-[11px] inline-block">
                          "{step.action_input}"
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sources & Feedback Footer */}
        {!isLoading && !message.isError && message.content && (
          <div className="px-6 py-4 bg-[var(--bg-surface)]/30 border-t border-[var(--border-subtle)] flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              {message.sources?.length > 0 && (
                <div className="flex items-center gap-1.5 text-[var(--text-tertiary)] mr-2">
                  <FileText size={12} /> <span className="text-[10px] font-bold uppercase tracking-wider">Sources</span>
                </div>
              )}
              {message.sources?.map((source, idx) => (
                <SourceCard key={idx} source={source} />
              ))}
            </div>
            
            <div className="flex items-center gap-2 ml-auto">
              {message.confidence !== undefined && (
                <span className={`text-[10px] font-bold px-2 py-1 rounded-lg border ${
                  message.confidence >= 0.7 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  message.confidence >= 0.4 ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                  'bg-red-500/10 text-red-400 border-red-500/20'
                }`}>
                  <ShieldCheck size={10} className="inline mr-1 -mt-0.5" />
                  {Math.round(message.confidence * 100)}% CONFIDENT
                </span>
              )}
              {!message.feedback && !message.requires_clarification && (
                <div className="flex items-center gap-1 border-l border-[var(--border-medium)] pl-2 ml-1">
                  <button onClick={() => onFeedback(5)} className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"><ThumbsUp size={13} /></button>
                  <button onClick={() => onFeedback(1)} className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-red-400 hover:bg-red-500/10 transition-colors"><ThumbsDown size={13} /></button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}