'use client';

/**
 * ChatInput.tsx
 * Week 5-6 (original) + Week 7-8 enhancements:
 * [x] Accepts an externalValue prop so PromptTemplates can pre-fill the input
 * [x] Retains all existing auto-resize, keyboard shortcuts, and generation state
 */

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';
import styles from './ChatInput.module.scss';

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  isGenerating: boolean;
  placeholder?: string;
  /** If set, overwrites the textarea value (used by template pre-fill) */
  externalValue?: string;
  /** Called after external value has been consumed so the parent can clear it */
  onExternalValueConsumed?: () => void;
}

export function ChatInput({
  onSendMessage,
  isGenerating,
  placeholder = 'Type your prompt here...',
  externalValue,
  onExternalValueConsumed,
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Handle template pre-fill: set input and focus textarea
  useEffect(() => {
    if (externalValue !== undefined && externalValue !== '') {
      setInput(externalValue);
      onExternalValueConsumed?.();
      // Focus and move cursor to end
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          const len = textareaRef.current.value.length;
          textareaRef.current.setSelectionRange(len, len);
        }
      }, 50);
    }
  }, [externalValue, onExternalValueConsumed]);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !isGenerating) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.composer}>
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isGenerating}
        rows={1}
        className={styles.textarea}
        aria-label="Write a prompt"
      />

      <div className={styles.sendArea}>
        <button
          onClick={handleSend}
          disabled={!input.trim() || isGenerating}
          type="button"
          aria-label={isGenerating ? 'Generating prompt' : 'Send prompt'}
          className={`${styles.sendButton} ${input.trim() && !isGenerating ? styles.sendEnabled : ''}`}
        >
          {isGenerating ? (
            <Sparkles size={18} className="animate-pulse text-indigo-300" />
          ) : (
            <Send size={18} className={input.trim() ? 'translate-x-[-1px] translate-y-[1px]' : ''} />
          )}
        </button>
      </div>

      {/* Hint bar */}
      <div className={styles.hint}>
        <span className={styles.keyboardHint}>
          Press{' '}
          <kbd>
            Enter
          </kbd>{' '}
          to send,{' '}
          <kbd>
            Shift + Enter
          </kbd>{' '}
          for new line.
        </span>
        <span className={styles.charCount}>{input.length} characters</span>
      </div>
    </div>
  );
}
