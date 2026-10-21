'use client';

import { useCallback, useEffect, useState } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { SessionSidebar } from '@/components/chat/SessionSidebar';
import { api } from '@/lib/api';

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

function formatSessionDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString();
}

export default function DashboardPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [resetKey, setResetKey] = useState(0);
  const [sessionsError, setSessionsError] = useState('');

  useEffect(() => {
    let cancelled = false;
    api.get<ChatSession[]>('/chat/sessions')
      .then(({ data }) => {
        if (!cancelled) setSessions(data);
      })
      .catch(() => {
        if (!cancelled) setSessionsError('Could not load your saved chats. Please refresh and try again.');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleNewChat = useCallback(() => {
    setSessionsError('');
    setActiveSession(null);
    setResetKey((key) => key + 1);
  }, []);

  const handleSessionCreated = useCallback((session: ChatSession) => {
    setSessions((current) => [session, ...current.filter((item) => item.id !== session.id)]);
    setActiveSession(session.id);
    setSessionsError('');
  }, []);

  const handleDeleteSession = useCallback(async (id: string) => {
    try {
      await api.delete(`/chat/sessions/${id}`);
      setSessions((current) => current.filter((session) => session.id !== id));
      if (activeSession === id) handleNewChat();
      setSessionsError('');
    } catch {
      setSessionsError('Could not delete that chat. Please try again.');
    }
  }, [activeSession, handleNewChat]);

  const mappedSessions = sessions.map((session) => ({
    ...session,
    date: formatSessionDate(session.created_at),
    isActive: session.id === activeSession,
  }));

  return (
    <div className="flex h-[calc(100vh-64px)] w-full">
      <div className="hidden md:block h-full">
        <SessionSidebar
          sessions={mappedSessions}
          onNewChat={handleNewChat}
          onSelectSession={setActiveSession}
          onDeleteSession={handleDeleteSession}
        />
      </div>

      <div className="relative flex-1 bg-slate-900/50 h-full min-w-0">
        <button
          type="button"
          onClick={handleNewChat}
          className="absolute right-3 top-3 z-20 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 shadow md:hidden"
        >
          New chat
        </button>
        {sessionsError && (
          <p className="px-4 pt-3 text-sm text-red-500" role="status">
            {sessionsError}
          </p>
        )}
        <ChatInterface
          sessionId={activeSession}
          resetKey={resetKey}
          onSessionCreated={handleSessionCreated}
        />
      </div>
    </div>
  );
}
