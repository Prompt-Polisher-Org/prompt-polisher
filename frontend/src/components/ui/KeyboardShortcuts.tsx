'use client';

import { useEffect, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ShortcutAction {
  /** The key to listen for (e.g. 'k', 'n', '/') */
  key: string;
  /** Modifier keys required */
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  /** Description for the shortcut palette */
  label: string;
  /** Action to execute */
  action: () => void;
}

interface KeyboardShortcutsProviderProps {
  shortcuts: ShortcutAction[];
  children: React.ReactNode;
}

/**
 * KeyboardShortcutsProvider — Global keyboard shortcut handler.
 * Wraps children and listens for keyboard combos.
 * Also provides a `?` shortcut to show a help palette.
 *
 * Task: Week 9-10 / Frontend Polish (task.md line 545)
 */
export function KeyboardShortcutsProvider({ shortcuts, children }: KeyboardShortcutsProviderProps) {
  const [showPalette, setShowPalette] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs/textareas
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        return;
      }

      // Show help palette on '?'
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setShowPalette((prev) => !prev);
        return;
      }

      // Escape closes palette
      if (e.key === 'Escape') {
        setShowPalette(false);
        return;
      }

      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? (e.ctrlKey || e.metaKey) : true;
        const shiftMatch = shortcut.shift ? e.shiftKey : true;
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (ctrlMatch && shiftMatch && keyMatch) {
          e.preventDefault();
          shortcut.action();
          return;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <>
      {children}

      <AnimatePresence>
        {showPalette && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowPalette(false)}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.5)',
                backdropFilter: 'blur(4px)',
                zIndex: 9998,
              }}
            />

            {/* Palette */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              style={{
                position: 'fixed',
                top: '20%',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '100%',
                maxWidth: '420px',
                background: '#1e293b',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '16px',
                padding: '1.5rem',
                zIndex: 9999,
                boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
              }}
            >
              <h3 style={{
                fontSize: '0.9375rem',
                fontWeight: 600,
                color: '#e2e8f0',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                ⌨️ Keyboard Shortcuts
                <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 400 }}>
                  Press <kbd style={{
                    padding: '2px 6px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '4px',
                    fontSize: '0.6875rem',
                  }}>Esc</kbd> to close
                </span>
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {shortcuts.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                    }}
                  >
                    <span style={{ fontSize: '0.8125rem', color: '#cbd5e1' }}>{s.label}</span>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      {s.ctrl && (
                        <kbd style={kbdStyle}>Ctrl</kbd>
                      )}
                      {s.shift && (
                        <kbd style={kbdStyle}>Shift</kbd>
                      )}
                      <kbd style={kbdStyle}>{s.key.toUpperCase()}</kbd>
                    </div>
                  </div>
                ))}

                {/* Always show the help shortcut */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '8px',
                  background: 'rgba(255,255,255,0.03)',
                }}>
                  <span style={{ fontSize: '0.8125rem', color: '#cbd5e1' }}>Show this help</span>
                  <kbd style={kbdStyle}>?</kbd>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

const kbdStyle: React.CSSProperties = {
  padding: '2px 8px',
  background: '#0f172a',
  border: '1px solid #334155',
  borderRadius: '4px',
  fontSize: '0.6875rem',
  fontFamily: 'var(--font-mono, monospace)',
  color: '#94a3b8',
  fontWeight: 500,
};
