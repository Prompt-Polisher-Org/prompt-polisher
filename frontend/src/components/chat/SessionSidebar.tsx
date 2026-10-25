import { useState } from 'react';
import { Plus, MessageSquare, Trash2 } from 'lucide-react';
import styles from './SessionSidebar.module.scss';

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
    <aside className={styles.sidebar} aria-label="Saved chats">
      
      {/* New Chat Button */}
      <div className={styles.top}>
        <button
          type="button"
          onClick={onNewChat}
          className={styles.newChat}
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>
      
      <div className={styles.sectionLabel}>
        Recent Chats
      </div>

      {/* Session List */}
      <div className={styles.list}>
        {sessions.length === 0 ? (
          <div className={styles.empty}>
            No recent chats
          </div>
        ) : (
          sessions.map(session => (
            <div 
              key={session.id}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => onSelectSession(session.id)}
              className={`${styles.session} ${session.isActive ? styles.sessionActive : ''}`}
            >
              <div className={styles.sessionTitle}>
                <MessageSquare size={16} aria-hidden="true" />
                <span>
                  {session.title}
                </span>
              </div>
              
              {hoveredId === session.id && (
                <button
                  type="button"
                  aria-label={`Delete chat: ${session.title}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                  className={styles.delete}
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
