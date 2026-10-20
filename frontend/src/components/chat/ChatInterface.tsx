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
import { ChatInput } from './ChatInput';
import { MessageBubble } from './MessageBubble';
import type { Message } from './MessageBubble';
import { PromptTemplates } from './PromptTemplates';
import { api } from '@/lib/api';

const uuidv4 = () => crypto.randomUUID();

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

interface StoredMessage {
  id: string;
  raw_content: string;
  polished_content: string | null;
  created_at: string;
}

interface ChatInterfaceProps {
  sessionId: string | null;
  resetKey: number;
  onSessionCreated: (session: ChatSession) => void;
}

export function ChatInterface({ sessionId, resetKey, onSessionCreated }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [pendingTemplate, setPendingTemplate] = useState<string | undefined>(undefined);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId);
  const [chatError, setChatError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const selectedSessionRef = useRef<string | null>(sessionId);
  const loadRequestRef = useRef(0);
  const previousResetKeyRef = useRef(resetKey);
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

  // Load persisted messages when the user opens a saved chat.
  useEffect(() => {
    if (sessionId === selectedSessionRef.current) {
      setCurrentSessionId(sessionId);
      return;
    }

    selectedSessionRef.current = sessionId;
    const requestId = ++loadRequestRef.current;
    wsRef.current?.close();
    setIsGenerating(false);
    setCurrentSessionId(sessionId);
    setMessages([]);
    setChatError('');

    if (!sessionId) return;

    api.get<StoredMessage[]>(`/chat/sessions/${sessionId}/messages`)
      .then(({ data }) => {
        if (requestId !== loadRequestRef.current) return;
        const restored = data.flatMap((item): Message[] => {
          const timestamp = new Date(item.created_at);
          const prompt: Message = {
            id: `${item.id}-user`,
            role: 'user',
            content: item.raw_content,
            timestamp,
          };
          if (!item.polished_content) return [prompt];
          return [prompt, {
            id: `${item.id}-ai`,
            role: 'ai',
            content: item.polished_content,
            timestamp,
            originalPrompt: item.raw_content,
          }];
        });
        setMessages(restored);
      })
      .catch(() => {
        if (requestId === loadRequestRef.current) {
          setChatError('Could not load this chat. Please try selecting it again.');
        }
      });
  }, [sessionId]);

  // An explicit New Chat click must clear the pane even when it is already blank.
  useEffect(() => {
    if (previousResetKeyRef.current === resetKey) return;
    previousResetKeyRef.current = resetKey;
    loadRequestRef.current += 1;
    selectedSessionRef.current = null;
    wsRef.current?.close();
    setCurrentSessionId(null);
    setMessages([]);
    setPendingTemplate(undefined);
    setChatError('');
    setIsGenerating(false);
  }, [resetKey]);

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
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isGenerating) return;
    setChatError('');
    setIsGenerating(true);
    genStartRef.current = Date.now();
    const aiMessageId = uuidv4();

    try {
      let targetSessionId = currentSessionId;
      if (!targetSessionId) {
        const { data: session } = await api.post<ChatSession>('/chat/sessions', {
          title: content.replace(/\s+/g, ' ').slice(0, 60) || 'New Polishing Session',
        });
        targetSessionId = session.id;
        selectedSessionRef.current = session.id;
        setCurrentSessionId(session.id);
        onSessionCreated(session);
      }

      const timestamp = new Date();
      setMessages((previous) => [...previous,
        { id: uuidv4(), role: 'user', content, timestamp },
        {
          id: aiMessageId,
          role: 'ai',
          content: '',
          timestamp,
          isStreaming: true,
          originalPrompt: content,
        },
      ]);

      const wsUrl = new URL(
        api.defaults.baseURL || 'http://localhost:8000/api/v1',
        window.location.origin,
      );
      wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl.pathname = `${wsUrl.pathname.replace(/\/$/, '')}/inference/ws/stream/${encodeURIComponent(targetSessionId)}`;
      wsUrl.search = '';
      const ws = new WebSocket(wsUrl.toString());
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            prompt: content,
            access_token: window.localStorage.getItem('access_token'),
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
          handleError(aiMessageId, data.error);
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
      setIsGenerating(false);
      setChatError('Could not start this chat. Check that you are signed in and the backend is running.');
    }
  };

  const handleError = (messageId: string, detail?: string) => {
    setMessages(prev =>
      prev.map(msg =>
        msg.id === messageId
          ? {
              ...msg,
              content: msg.content + `\n\n*${detail || 'Connection failed. Please try again.'}*`,
              isStreaming: false,
              generationMs: Date.now() - genStartRef.current,
            }
          : msg,
      ),
    );
    setIsGenerating(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-60px)] md:h-[calc(100vh-80px)] max-w-4xl mx-auto w-full relative">

      {/* Message / Template area */}
      <div className="flex-1 overflow-y-auto px-3 md:px-4 py-4 md:py-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {chatError && (
          <p className="mb-4 text-center text-sm text-red-500" role="alert">
            {chatError}
          </p>
        )}
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
            key={sessionId ?? `new-${resetKey}`}
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
