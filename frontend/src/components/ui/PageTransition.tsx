'use client';

/**
 * PageTransition.tsx — Week 9-10
 *
 * Wraps page content with smooth Framer Motion animations that trigger
 * on route changes. Provides a fade + subtle slide-up transition.
 *
 * Usage: Wrap {children} in any layout.tsx:
 *   <PageTransition pathname={pathname}>{children}</PageTransition>
 */

import { motion, AnimatePresence } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
  /** The current pathname — used as the animation key so transitions fire on route change */
  pathname: string;
}

const pageVariants = {
  initial: {
    opacity: 0,
    y: 12,
    filter: 'blur(4px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.3,
      ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    filter: 'blur(2px)',
    transition: {
      duration: 0.2,
      ease: [0.55, 0.06, 0.68, 0.19] as [number, number, number, number],
    },
  },
};

export function PageTransition({ children, pathname }: PageTransitionProps) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        style={{ width: '100%', height: '100%' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
