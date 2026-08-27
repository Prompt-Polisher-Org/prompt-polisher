'use client';

import { useState, useEffect } from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * OfflineBanner — Detects loss of network connectivity and displays
 * a persistent banner at the top of the viewport. Automatically hides
 * when connectivity is restored.
 *
 * Task: Week 9-10 / Frontend Polish (task.md line 539)
 */
export function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const goOffline = () => {
      setIsOffline(true);
      setWasOffline(true);
    };
    const goOnline = () => {
      setIsOffline(false);
      // Show the "back online" message briefly
      setTimeout(() => setWasOffline(false), 3000);
    };

    // Check initial state
    if (!navigator.onLine) {
      goOffline();
    }

    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);

    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
    };
  }, []);

  return (
    <AnimatePresence>
      {isOffline && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.75rem',
            padding: '0.625rem 1rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          }}
        >
          <WifiOff size={16} />
          <span>You are offline. Some features may be unavailable.</span>
          <button
            onClick={() => window.location.reload()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '0.25rem 0.75rem',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </motion.div>
      )}

      {!isOffline && wasOffline && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            background: 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.75rem',
            padding: '0.625rem 1rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          }}
        >
          ✅ Back online
        </motion.div>
      )}
    </AnimatePresence>
  );
}
