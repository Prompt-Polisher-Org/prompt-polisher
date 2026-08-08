import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  isGenerating: boolean;
  placeholder?: string;
}

export function ChatInput({ onSendMessage, isGenerating, placeholder = "Type your prompt here..." }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
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
    <div className="relative group flex items-end bg-slate-800/80 border border-slate-700/80 focus-within:border-indigo-500/50 rounded-2xl backdrop-blur-xl shadow-lg transition-colors duration-200 p-2 pl-4">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isGenerating}
        rows={1}
        className="flex-grow bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none resize-none py-3 max-h-[150px] overflow-y-auto scrollbar-hide text-[15px] leading-relaxed disabled:opacity-50"
      />
      
      <div className="flex flex-col justify-end ml-2 pb-1 shrink-0">
        <button
          onClick={handleSend}
          disabled={!input.trim() || isGenerating}
          className={`flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200 ${
            input.trim() && !isGenerating
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 hover:scale-105'
              : 'bg-slate-700/50 text-slate-500 cursor-not-allowed'
          }`}
        >
          {isGenerating ? (
            <Sparkles size={18} className="animate-pulse text-indigo-300" />
          ) : (
            <Send size={18} className={input.trim() ? "translate-x-[-1px] translate-y-[1px]" : ""} />
          )}
        </button>
      </div>

      {/* Character count / hints */}
      <div className="absolute -bottom-6 right-2 text-xs text-slate-500">
        <span className="hidden sm:inline">Press <kbd className="font-sans px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">Enter</kbd> to send, <kbd className="font-sans px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">Shift + Enter</kbd> for new line.</span>
        <span className="ml-3 font-mono">{input.length}</span>
      </div>
    </div>
  );
}
