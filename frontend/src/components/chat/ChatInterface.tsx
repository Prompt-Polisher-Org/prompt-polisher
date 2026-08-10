'use client';

/**
 * ChatInterface.tsx
 * Week 5-6 (original) + Week 7-8 enhancements:
 * [x] Cursor blink + stop-generating button (via MessageBubble)
 * [x] Token count + generation timer (tracked here, passed to MessageBubble)
 * [x] Template pre-fill (PromptTemplates → ChatInput via pendingTemplate state)
 * [x] Comparison view — originalPrompt stored on each AI message
 * [x] Empty state shows PromptTemplates component instead of plain text
 */

import { useState, useRef, useEffect } from 'react';

const uuidv4 = () => crypto.randomUUID();
import { ChatInput } from './ChatInput';
import { MessageBubble, Message } from './MessageBubble';
import { PromptTemplates } from './PromptTemplates';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  // Track generation start time for elapsed-ms display
  const genStartRef = useRef<number>(0);

  // Auto-scroll on new messages / streaming updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Close WebSocket on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  // ── Stop Generating ──────────────────────────────────────────────────────
  const handleStopGenerating = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsGenerating(false);
    setMessages(prev =>
      prev.map(msg =>
        msg.isStreaming
          ? {
              ...msg,
              isStreaming: false,
              generationMs: Date.now() - genStartRef.current,
            }
          : msg,
      ),
    );
  };

  // ── Send Message ─────────────────────────────────────────────────────────
  const handleSendMessage = (content: string) => {
    if (!content.trim() || isGenerating) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsGenerating(true);
    genStartRef.current = Date.now();

    const aiMessageId = uuidv4();

    // Placeholder AI bubble (streaming)
    setMessages(prev => [
      ...prev,
      {
        id: aiMessageId,
        role: 'ai',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
        originalPrompt: content, // store so comparison view can diff
      },
    ]);

    // ── WebSocket connection ─────────────────────────────────────────────
    try {
      const sessionId = uuidv4();
      const wsUrl = `ws://localhost:8000/api/v1/inference/ws/stream/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            prompt: content,
            preferences_override: { temperature: 0.7 },
          }),
        );
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'token') {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === aiMessageId
                ? { ...msg, content: msg.content + data.text }
                : msg,
            ),
          );
        } else if (data.type === 'done') {
          const elapsed = Date.now() - genStartRef.current;
          setMessages(prev =>
            prev.map(msg =>
              msg.id === aiMessageId
                ? {
                    ...msg,
                    content: data.full_text || msg.content,
                    isStreaming: false,
                    generationMs: elapsed,
                  }
                : msg,
            ),
          );
          setIsGenerating(false);
          ws.close();
        } else if (data.error) {
          console.error('WS error:', data.error);
          handleError(aiMessageId);
        }
      };

      ws.onerror = () => handleError(aiMessageId);

      ws.onclose = () => {
        setIsGenerating(false);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === aiMessageId && msg.isStreaming
              ? {
                  ...msg,
                  isStreaming: false,
                  generationMs: Date.now() - genStartRef.current,
                }
              : msg,
          ),
        );
      };
    } catch (err) {
      console.error('Failed to initiate generation:', err);
      handleError(aiMessageId);
    }
  };

  const handleError = (messageId: string) => {
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId
          ? {
              ...msg,
              content:
                msg.content + '\n\n*[Connection failed. Please try again.]*',
              isStreaming: false,
              generationMs: Date.now() - genStartRef.current,
            }
          : msg,
      ),
    );
    setIsGenerating(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto w-full">

      {/* Message / Template area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {messages.length === 0 ? (
          /* ── Empty state: show template quick-starts ── */
          <div className="flex flex-col h-full">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center border border-slate-700/50 shadow-inner mb-4 mx-auto">
                <span className="text-3xl">✨</span>
              </div>
              <h2 className="text-xl font-semibold text-slate-200 mb-2">
                What would you like to polish?
              </h2>
              <p className="text-sm text-slate-400 max-w-sm mx-auto">
                Start with a template below or type your own prompt.
              </p>
            </div>

            <PromptTemplates onSelectTemplate={(t) => setPendingTemplate(t)} />
          </div>
        ) : (
          <div className="flex flex-col pb-4">
            {messages.map(msg => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onStopGenerating={msg.isStreaming ? handleStopGenerating : undefined}
              />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="p-4 bg-slate-900/50 backdrop-blur-sm border-t border-slate-800/50 z-10">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            isGenerating={isGenerating}
            externalValue={pendingTemplate}
            onExternalValueConsumed={() => setPendingTemplate(undefined)}
          />
        </div>
      </div>
    </div>
  );
}
