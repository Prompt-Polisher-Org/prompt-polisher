import { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatInput } from './ChatInput';
import { MessageBubble, Message } from './MessageBubble';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSendMessage = (content: string) => {
    if (!content.trim() || isGenerating) return;

    // Add user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsGenerating(true);

    // Prepare AI response placeholder
    const aiMessageId = uuidv4();
    setMessages(prev => [
      ...prev,
      {
        id: aiMessageId,
        role: 'ai',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      }
    ]);

    // Connect to WebSocket and send prompt
    try {
      // In production, this URL should be loaded from env vars
      const session_id = uuidv4(); // Mock session ID for now
      const wsUrl = `ws://localhost:8000/api/v1/inference/ws/stream/${session_id}`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ 
          prompt: content,
          preferences_override: { temperature: 0.7 } 
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          setMessages(prev => prev.map(msg => {
            if (msg.id === aiMessageId) {
              return { ...msg, content: msg.content + data.text };
            }
            return msg;
          }));
        } else if (data.type === 'done') {
          setMessages(prev => prev.map(msg => {
            if (msg.id === aiMessageId) {
              return { ...msg, content: data.full_text || msg.content, isStreaming: false };
            }
            return msg;
          }));
          setIsGenerating(false);
          ws.close();
        } else if (data.error) {
          console.error('WebSocket error:', data.error);
          handleError(aiMessageId);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket connection error:', error);
        handleError(aiMessageId);
      };

      ws.onclose = () => {
        setIsGenerating(false);
        setMessages(prev => prev.map(msg => {
          if (msg.id === aiMessageId && msg.isStreaming) {
            return { ...msg, isStreaming: false };
          }
          return msg;
        }));
      };
      
    } catch (err) {
      console.error('Failed to initiate generation:', err);
      handleError(aiMessageId);
    }
  };

  const handleError = (messageId: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        return { 
          ...msg, 
          content: msg.content + '\n\n*[Connection failed. Please try again later.]*', 
          isStreaming: false 
        };
      }
      return msg;
    }));
    setIsGenerating(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto w-full">
      {/* Chat History Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
            <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center border border-slate-700/50 shadow-inner mb-4">
              <span className="text-3xl">✨</span>
            </div>
            <h2 className="text-xl font-medium text-slate-200">What would you like to polish?</h2>
            <p className="text-sm max-w-sm text-center">
              Paste your raw thoughts or a draft prompt, and I will optimize it for clarity, structure, and effectiveness.
            </p>
          </div>
        ) : (
          <div className="flex flex-col pb-4">
            {messages.map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-900/50 backdrop-blur-sm border-t border-slate-800/50 z-10">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSendMessage={handleSendMessage} isGenerating={isGenerating} />
        </div>
      </div>
    </div>
  );
}
