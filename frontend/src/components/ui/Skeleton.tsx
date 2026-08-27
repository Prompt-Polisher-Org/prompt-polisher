'use client';

import React from 'react';

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
}

/**
 * Skeleton — A shimmer loading placeholder.
 * Use instead of spinners for a more polished content-loading experience.
 *
 * Task: Week 9-10 / Frontend Polish (task.md line 538)
 */
export function Skeleton({
  width = '100%',
  height = '1rem',
  borderRadius = '6px',
  className = '',
}: SkeletonProps) {
  return (
    <div
      className={className}
      style={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, rgba(30,41,59,0.6) 25%, rgba(51,65,85,0.4) 50%, rgba(30,41,59,0.6) 75%)',
        backgroundSize: '200% 100%',
        animation: 'skeleton-shimmer 1.5s ease-in-out infinite',
      }}
    />
  );
}

/**
 * SkeletonText — Multiple lines of shimmer placeholders.
 */
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '60%' : '100%'}
          height="0.875rem"
        />
      ))}
    </div>
  );
}

/**
 * SkeletonCard — A card-shaped skeleton block for dashboard cards.
 */
export function SkeletonCard() {
  return (
    <div style={{
      padding: '1.5rem',
      background: 'rgba(30, 41, 59, 0.5)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
    }}>
      <Skeleton width="40%" height="1.25rem" />
      <SkeletonText lines={3} />
      <Skeleton width="30%" height="2rem" borderRadius="8px" />
    </div>
  );
}

/**
 * SkeletonChatMessage — A chat message skeleton (avatar + bubble).
 */
export function SkeletonChatMessage({ align = 'left' }: { align?: 'left' | 'right' }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: align === 'right' ? 'flex-end' : 'flex-start',
      marginBottom: '1.5rem',
      gap: '0.75rem',
      flexDirection: align === 'right' ? 'row-reverse' : 'row',
    }}>
      <Skeleton width="32px" height="32px" borderRadius="50%" />
      <div style={{
        display: 'flex', flexDirection: 'column', gap: '0.5rem',
        maxWidth: '65%',
      }}>
        <Skeleton height="2.5rem" borderRadius="12px" />
        <Skeleton width="45%" height="0.75rem" />
      </div>
    </div>
  );
}
