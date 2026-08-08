import { useState, useEffect } from 'react';
import { Plus, MessageSquare, MoreHorizontal, Trash2 } from 'lucide-react';

interface Session {
  id: string;
  title: string;
  date: string;
  isActive?: boolean;
}

interface SessionSidebarProps {
  sessions: Session[];
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
}

export function SessionSidebar({ sessions, onNewChat, onSelectSession, onDeleteSession }: SessionSidebarProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="flex flex-col h-full bg-slate-900/40 border-r border-slate-800/60 w-64 flex-shrink-0">
      
      {/* New Chat Button */}
      <div className="p-4">
        <button 
          onClick={onNewChat}
          className="flex items-center justify-center w-full gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl transition-colors font-medium shadow-sm"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>
      
      <div className="px-4 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
        Recent Chats
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent pb-4">
        {sessions.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-slate-500">
            No recent chats
          </div>
        ) : (
          sessions.map(session => (
            <div 
              key={session.id}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onSelectSession(session.id)}
              className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                session.isActive 
                  ? 'bg-slate-800/80 text-indigo-300' 
                  : 'hover:bg-slate-800/40 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <MessageSquare size={16} className={session.isActive ? 'text-indigo-400' : 'text-slate-500'} />
                <span className="text-sm truncate">
                  {session.title}
                </span>
              </div>
              
              {hoveredId === session.id && (
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  className="p-1 text-slate-500 hover:text-red-400 hover:bg-slate-700/50 rounded transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
