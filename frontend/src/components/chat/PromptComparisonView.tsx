'use client';

/**
 * PromptComparisonView.tsx
 * Week 7-8 / Enhanced Chat UI - Prompt Comparison
 * [x] Side-by-side layout: "Your Prompt" vs "Optimised Prompt"
 * [x] Diff highlighting (changed words/lines shown in amber)
 * [x] Toggle between side-by-side and inline view
 * [x] Copy as plain text or markdown
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, Columns2, AlignLeft, ChevronDown, ChevronUp } from 'lucide-react';

interface PromptComparisonViewProps {
  original: string;
  optimized: string;
  /** whether to start collapsed (e.g. embedded inside a chat message) */
  collapsible?: boolean;
}

/** Word-level diff: returns tokens tagged as 'same' | 'removed' | 'added' */
function computeWordDiff(original: string, optimized: string) {
  const origWords = original.split(/(\s+)/);
  const optWords = optimized.split(/(\s+)/);
  const origSet = new Set(origWords.map(w => w.toLowerCase().trim()).filter(Boolean));
  const optSet = new Set(optWords.map(w => w.toLowerCase().trim()).filter(Boolean));

  const origTagged = origWords.map(w => ({
    text: w,
    type: optSet.has(w.toLowerCase().trim()) || !w.trim() ? 'same' : 'removed',
  }));
  const optTagged = optWords.map(w => ({
    text: w,
    type: origSet.has(w.toLowerCase().trim()) || !w.trim() ? 'same' : 'added',
  }));

  return { origTagged, optTagged };
}

function DiffText({ tokens }: { tokens: { text: string; type: string }[] }) {
  return (
    <p className="whitespace-pre-wrap leading-7 text-sm text-slate-200 font-mono">
      {tokens.map((t, i) => {
        if (t.type === 'removed') {
          return (
            <span key={i} className="bg-red-500/15 text-red-300 rounded px-0.5">
              {t.text}
            </span>
          );
        }
        if (t.type === 'added') {
          return (
            <span key={i} className="bg-emerald-500/15 text-emerald-300 rounded px-0.5">
              {t.text}
            </span>
          );
        }
        return <span key={i}>{t.text}</span>;
      })}
    </p>
  );
}

type CopyMode = 'text' | 'markdown';

function CopyButton({ text, mode }: { text: string; mode: CopyMode }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const content =
      mode === 'markdown' ? `\`\`\`\n${text}\n\`\`\`` : text;
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleCopy}
      title={mode === 'markdown' ? 'Copy as Markdown' : 'Copy as plain text'}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium
                 bg-slate-700/60 hover:bg-slate-700 text-slate-300 hover:text-white
                 border border-slate-600/50 transition-all duration-150"
    >
      {copied ? (
        <Check size={12} className="text-emerald-400" />
      ) : (
        <Copy size={12} />
      )}
      {copied ? 'Copied!' : mode === 'markdown' ? 'Copy MD' : 'Copy'}
    </button>
  );
}

export function PromptComparisonView({
  original,
  optimized,
  collapsible = false,
}: PromptComparisonViewProps) {
  const [view, setView] = useState<'split' | 'inline'>('split');
  const [collapsed, setCollapsed] = useState(false);

  const { origTagged, optTagged } = useMemo(
    () => computeWordDiff(original, optimized),
    [original, optimized]
  );

  const addedCount = optTagged.filter(t => t.type === 'added').length;
  const removedCount = origTagged.filter(t => t.type === 'removed').length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 rounded-2xl border border-slate-700/60 bg-slate-800/60 backdrop-blur-sm overflow-hidden shadow-xl shadow-slate-900/30"
    >
      {/* Header toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700/50 bg-slate-800/80">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Comparison
          </span>
          {/* Diff stats pills */}
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-medium border border-emerald-500/20">
            +{addedCount}
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-[11px] font-medium border border-red-500/20">
            −{removedCount}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-lg border border-slate-700 overflow-hidden">
            <button
              onClick={() => setView('split')}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors ${
                view === 'split'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Columns2 size={13} />
              Split
            </button>
            <button
              onClick={() => setView('inline')}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs transition-colors ${
                view === 'inline'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <AlignLeft size={13} />
              Inline
            </button>
          </div>
          {/* Collapse toggle */}
          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-1 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
            >
              {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {view === 'split' ? (
              /* ── SPLIT VIEW ── */
              <div className="grid grid-cols-2 divide-x divide-slate-700/50">
                {/* Left: Original */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Your Prompt
                    </span>
                    <CopyButton text={original} mode="text" />
                  </div>
                  <DiffText tokens={origTagged} />
                </div>
                {/* Right: Optimized */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                      ✨ Optimised
                    </span>
                    <div className="flex gap-2">
                      <CopyButton text={optimized} mode="text" />
                      <CopyButton text={optimized} mode="markdown" />
                    </div>
                  </div>
                  <DiffText tokens={optTagged} />
                </div>
              </div>
            ) : (
              /* ── INLINE VIEW ── */
              <div className="p-4 space-y-5">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Your Prompt
                    </span>
                    <CopyButton text={original} mode="text" />
                  </div>
                  <div className="rounded-xl bg-slate-900/50 p-3 border border-slate-700/40">
                    <DiffText tokens={origTagged} />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-slate-700/50" />
                  <span className="text-xs text-indigo-400 font-medium">↓ optimised</span>
                  <div className="h-px flex-1 bg-slate-700/50" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                      ✨ Optimised Prompt
                    </span>
                    <div className="flex gap-2">
                      <CopyButton text={optimized} mode="text" />
                      <CopyButton text={optimized} mode="markdown" />
                    </div>
                  </div>
                  <div className="rounded-xl bg-slate-900/50 p-3 border border-indigo-500/20">
                    <DiffText tokens={optTagged} />
                  </div>
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 px-4 py-2 bg-slate-900/30 border-t border-slate-700/40 text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded bg-emerald-500/20 border border-emerald-500/30" />
                Added
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded bg-red-500/20 border border-red-500/30" />
                Removed
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
