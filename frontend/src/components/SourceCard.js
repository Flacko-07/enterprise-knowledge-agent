'use client';

import { FileText } from 'lucide-react';

export default function SourceCard({ source }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg 
      bg-[var(--bg-card)] border border-[var(--border-medium)] text-[11px] font-medium text-[var(--text-secondary)]
      hover:border-indigo-500/30 hover:text-indigo-300 hover:bg-indigo-500/5 transition-all duration-200 cursor-default shadow-sm">
      <FileText size={10} className="text-indigo-400" />
      <span className="truncate max-w-[120px] font-semibold">{source.document}</span>
      {source.page && (
        <span className="text-[var(--text-tertiary)] font-mono text-[10px]">p{source.page}</span>
      )}
    </div>
  );
}