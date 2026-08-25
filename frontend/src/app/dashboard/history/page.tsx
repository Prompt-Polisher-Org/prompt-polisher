'use client';

/**
 * dashboard/history/page.tsx — Chat History page
 * Week 7-8 / Enhanced Chat UI
 * [x] List all past sessions with titles and dates
 * [x] Search/filter conversations by title
 * [x] Click to reopen a session (navigates to dashboard)
 * [x] Delete session with confirmation modal
 */

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Search,
  Trash2,
  ExternalLink,
  Calendar,
  Clock,
  AlertTriangle,
  X,
  ChevronRight,
} from 'lucide-react';

interface Session {
  id: string;
  title: string;
  preview: string;
  messageCount: number;
  createdAt: string;
  updatedAt: string;
}

// ── Mock data — replace with API call to GET /api/v1/chat/sessions ────────────
const MOCK_SESSIONS: Session[] = [
  {
    id: '1',
    title: 'Make this Python script faster',
    preview: 'I have a script that processes 10k records and takes 5 minutes...',
    messageCount: 6,
    createdAt: '2026-08-09T10:30:00Z',
    updatedAt: '2026-08-09T10:45:00Z',
  },
  {
    id: '2',
    title: 'Write a cold email to investors',
    preview: 'We need to reach out to 20 seed-stage investors for our SaaS...',
    messageCount: 4,
    createdAt: '2026-08-08T14:00:00Z',
    updatedAt: '2026-08-08T14:20:00Z',
  },
  {
    id: '3',
    title: 'Explain transformer architecture',
    preview: 'Can you explain how transformers work for someone who knows Python...',
    messageCount: 8,
    createdAt: '2026-08-07T09:15:00Z',
    updatedAt: '2026-08-07T09:50:00Z',
  },
  {
    id: '4',
    title: 'Marketing copy for Product Hunt launch',
    preview: 'Write a tagline and description for our prompt optimisation tool...',
    messageCount: 10,
    createdAt: '2026-08-06T16:00:00Z',
    updatedAt: '2026-08-06T16:40:00Z',
  },
  {
    id: '5',
    title: 'SQL query optimisation for analytics dashboard',
    preview: 'This query is taking 30 seconds and I need it under 500ms...',
    messageCount: 5,
    createdAt: '2026-08-05T11:00:00Z',
    updatedAt: '2026-08-05T11:30:00Z',
  },
  {
    id: '6',
    title: 'Write a performance review for my team lead',
    preview: 'My team lead Jane has been exceptional this quarter. I want to...',
    messageCount: 3,
    createdAt: '2026-08-04T13:00:00Z',
    updatedAt: '2026-08-04T13:15:00Z',
  },
];

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ── Delete Confirmation Modal ─────────────────────────────────────────────────
function DeleteConfirmModal({
  session,
  onConfirm,
  onCancel,
}: {
  session: Session;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        transition={{ duration: 0.15 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl p-6 max-w-md w-full mx-4"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20">
            <AlertTriangle size={18} className="text-red-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Delete conversation?</h3>
            <p className="text-sm text-slate-400">This action cannot be undone.</p>
          </div>
        </div>

        <div className="bg-slate-900/50 rounded-xl p-3 mb-5 border border-slate-700/50">
          <p className="text-sm text-slate-300 font-medium truncate">{session.title}</p>
          <p className="text-xs text-slate-500 mt-0.5">{session.messageCount} messages</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-700/60 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-600/50 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-sm font-medium shadow-lg shadow-red-600/20 transition-colors"
          >
            Delete
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function HistoryPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>(MOCK_SESSIONS);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingSession, setDeletingSession] = useState<Session | null>(null);

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const q = searchQuery.toLowerCase();
    return sessions.filter(
      s =>
        s.title.toLowerCase().includes(q) ||
        s.preview.toLowerCase().includes(q),
    );
  }, [sessions, searchQuery]);

  const handleDelete = (session: Session) => {
    setDeletingSession(session);
  };

  const confirmDelete = () => {
    if (!deletingSession) return;
    setSessions(prev => prev.filter(s => s.id !== deletingSession.id));
    setDeletingSession(null);
  };

  const handleOpen = (session: Session) => {
    // Navigate to dashboard with session selected
    // In a full implementation, pass session ID via query param or state
    router.push(`/dashboard?session=${session.id}`);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Chat History</h1>
        <p className="text-slate-400 text-sm">
          {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Search bar */}
      <div className="relative mb-6">
        <Search
          size={16}
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations..."
          className="w-full pl-10 pr-10 py-3 bg-slate-800/60 border border-slate-700/60
                     rounded-xl text-slate-200 placeholder-slate-500 text-sm
                     focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/20
                     transition-colors"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Session list */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <MessageSquare size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">
            {searchQuery ? 'No conversations match your search.' : 'No conversations yet.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {filtered.map((session, i) => (
              <motion.div
                key={session.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: i * 0.04 }}
                className="group flex items-center gap-4 p-4 rounded-2xl
                           bg-slate-800/50 border border-slate-700/50
                           hover:border-slate-600/70 hover:bg-slate-800/80
                           transition-all duration-200 cursor-pointer"
                onClick={() => handleOpen(session)}
              >
                {/* Icon */}
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-indigo-600/15
                                border border-indigo-500/20 flex items-center justify-center
                                group-hover:bg-indigo-600/25 transition-colors">
                  <MessageSquare size={18} className="text-indigo-400" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-200 truncate group-hover:text-white transition-colors">
                    {session.title}
                  </p>
                  <p className="text-xs text-slate-500 truncate mt-0.5">
                    {session.preview}
                  </p>
                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-slate-600">
                    <span className="flex items-center gap-1">
                      <Calendar size={10} />
                      {formatDate(session.updatedAt)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatTime(session.updatedAt)}
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageSquare size={10} />
                      {session.messageCount} messages
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleOpen(session);
                    }}
                    title="Open conversation"
                    className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-indigo-400 transition-colors"
                  >
                    <ExternalLink size={14} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(session);
                    }}
                    title="Delete conversation"
                    className="p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                  <ChevronRight size={14} className="text-slate-600" />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Delete confirmation modal */}
      <AnimatePresence>
        {deletingSession && (
          <DeleteConfirmModal
            session={deletingSession}
            onConfirm={confirmDelete}
            onCancel={() => setDeletingSession(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
