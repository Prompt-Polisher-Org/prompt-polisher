'use client';

/**
 * MessageBubble.tsx
 * Week 5-6 (original) + Week 7-8 enhancements:
 * [x] Cursor blink animation during generation
 * [x] Token count display on completed AI messages
 * [x] Generation time display
 * [x] Copy button with animation (plain text + toast feedback)
 * [x] "Stop generating" callback support
 * [x] Comparison view toggle (shows PromptComparisonView when original prompt is stored)
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Copy, Check, Timer, Hash, SplitSquareVertical } from 'lucide-react';
import { PromptComparisonView } from './PromptComparisonView';

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  /** elapsed ms when streaming finished — set by ChatInterface */
  generationMs?: number;
  /** the original user prompt this AI message was generated in response to */
  originalPrompt?: string;
}

interface MessageBubbleProps {
  message: Message;
  onStopGenerating?: () => void;
}

/** Estimate token count (≈ 4 chars per token). */
function estimateTokens(text: string): number {
  return Math.max(1, Math.round(text.length / 4));
}

function formatMs(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function MessageBubble({ message, onStopGenerating }: MessageBubbleProps) {
  const isAi = message.role === 'ai';
  const [copied, setCopied] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const tokenCount = isAi && !message.isStreaming ? estimateTokens(message.content) : null;
  const hasComparison = isAi && !message.isStreaming && !!message.originalPrompt;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex w-full mb-6 ${isAi ? 'justify-start' : 'justify-end'}`}
    >
      <div className={`flex max-w-[85%] ${isAi ? 'flex-row' : 'flex-row-reverse'}`}>

        {/* Avatar */}
        <div
          className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full mt-1
            ${isAi
              ? 'bg-indigo-600/20 text-indigo-400 mr-3 ring-1 ring-indigo-500/30'
              : 'bg-slate-700 text-slate-300 ml-3'
            }`}
        >
          {isAi ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Bubble + meta */}
        <div className="flex flex-col relative group min-w-0">
          {/* Bubble */}
          <div
            className={`px-5 py-3.5 rounded-2xl ${
              isAi
                ? 'bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-tl-sm backdrop-blur-md shadow-lg shadow-slate-900/20'
                : 'bg-indigo-600 text-white rounded-tr-sm shadow-md shadow-indigo-600/20'
            }`}
          >
            <div className="whitespace-pre-wrap leading-relaxed text-[15px]">
              {message.content}

              {/* Cursor blink animation during streaming */}
              {message.isStreaming && (
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                  className="inline-block w-[2px] h-[1.1em] ml-0.5 bg-indigo-400 align-middle"
                />
              )}
            </div>

            {/* Stop generating button — shown inline when streaming */}
            {message.isStreaming && onStopGenerating && (
              <button
                onClick={onStopGenerating}
                className="mt-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                           bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300
                           border border-red-500/20 text-xs font-medium transition-all duration-150"
              >
                <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                Stop generating
              </button>
            )}
          </div>

          {/* Meta row: timestamp + token count + timer + actions */}
          <div
            className={`flex items-center mt-1.5 gap-2 text-[11px] text-slate-500
              ${isAi ? 'justify-start ml-1' : 'justify-end mr-1'}`}
          >
            <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>

            {/* Token count — shown after streaming completes */}
            {tokenCount !== null && (
              <span className="flex items-center gap-0.5 opacity-60 hover:opacity-100 transition-opacity">
                <Hash size={10} />
                {tokenCount} tokens
              </span>
            )}

            {/* Generation time */}
            {isAi && !message.isStreaming && message.generationMs && (
              <span className="flex items-center gap-0.5 opacity-60 hover:opacity-100 transition-opacity">
                <Timer size={10} />
                {formatMs(message.generationMs)}
              </span>
            )}

            {/* Action buttons — only on completed AI messages */}
            {isAi && !message.isStreaming && (
              <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {/* Copy */}
                <button
                  onClick={handleCopy}
                  title="Copy message"
                  className="flex items-center gap-1 hover:text-indigo-400 transition-colors"
                >
                  {copied ? (
                    <Check size={12} className="text-emerald-400" />
                  ) : (
                    <Copy size={12} />
                  )}
                  {copied ? 'Copied' : 'Copy'}
                </button>

                {/* Compare toggle */}
                {hasComparison && (
                  <button
                    onClick={() => setShowComparison(!showComparison)}
                    title="Toggle comparison view"
                    className={`flex items-center gap-1 transition-colors ${
                      showComparison ? 'text-indigo-400' : 'hover:text-indigo-400'
                    }`}
                  >
                    <SplitSquareVertical size={12} />
                    {showComparison ? 'Hide diff' : 'Compare'}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Comparison view — animated slide-in */}
          <AnimatePresence>
            {showComparison && hasComparison && (
              <PromptComparisonView
                original={message.originalPrompt!}
                optimized={message.content}
                collapsible
              />
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
