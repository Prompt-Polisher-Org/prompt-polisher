'use client';

import { useState } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { SessionSidebar } from '@/components/chat/SessionSidebar';
import { v4 as uuidv4 } from 'uuid';

export default function DashboardPage() {
  const [sessions, setSessions] = useState([
    { id: '1', title: 'Make this python script faster', date: 'Today' },
    { id: '2', title: 'Write a cold email to investors', date: 'Yesterday' },
  ]);
  const [activeSession, setActiveSession] = useState<string | null>(null);

  const handleNewChat = () => {
    setActiveSession(null);
    // Logic to reset chat interface state will be handled inside ChatInterface 
    // or lifted here later. For now, it unselects the active session.
  };

  const handleDeleteSession = (id: string) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSession === id) setActiveSession(null);
  };

  // Ensure active session flag is set correctly
  const mappedSessions = sessions.map(s => ({
    ...s,
    isActive: s.id === activeSession
  }));

  return (
    <div className="flex h-[calc(100vh-64px)] w-full">
      {/* Secondary Sidebar for Chat Sessions */}
      <div className="hidden md:block h-full">
        <SessionSidebar 
          sessions={mappedSessions}
          onNewChat={handleNewChat}
          onSelectSession={setActiveSession}
          onDeleteSession={handleDeleteSession}
        />
      </div>

      {/* Main Chat Interface */}
      <div className="flex-1 bg-slate-900/50 h-full">
        <ChatInterface key={activeSession || 'new'} />
      </div>
    </div>
  );
}
