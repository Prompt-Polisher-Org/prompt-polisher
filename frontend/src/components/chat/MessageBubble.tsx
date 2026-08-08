import { motion } from 'framer-motion';
import { Bot, User, Copy, Check } from 'lucide-react';
import { useState } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAi = message.role === 'ai';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full mb-6 ${isAi ? 'justify-start' : 'justify-end'}`}
    >
      <div className={`flex max-w-[85%] ${isAi ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full mt-1 ${isAi ? 'bg-indigo-600/20 text-indigo-400 mr-3' : 'bg-slate-700 text-slate-300 ml-3'}`}>
          {isAi ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Bubble */}
        <div className="flex flex-col relative group">
          <div 
            className={`px-5 py-3.5 rounded-2xl ${
              isAi 
                ? 'bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-tl-sm backdrop-blur-md shadow-lg shadow-slate-900/20' 
                : 'bg-indigo-600 text-white rounded-tr-sm shadow-md shadow-indigo-600/20'
            }`}
          >
            <div className="whitespace-pre-wrap leading-relaxed">
              {message.content}
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse" />
              )}
            </div>
          </div>
          
          {/* Action Row & Timestamp */}
          <div className={`flex items-center mt-1 space-x-2 text-[11px] text-slate-500 ${isAi ? 'justify-start ml-1' : 'justify-end mr-1'}`}>
            <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            
            {isAi && !message.isStreaming && (
              <button 
                onClick={handleCopy}
                className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center hover:text-indigo-400"
              >
                {copied ? <Check size={12} className="mr-1 text-emerald-400" /> : <Copy size={12} className="mr-1" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
