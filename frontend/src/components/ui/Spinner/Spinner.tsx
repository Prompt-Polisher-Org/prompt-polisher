import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import styles from './Spinner.module.scss';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  return (
    <div
      className={twMerge(clsx(styles.spinner, styles[size], className))}
      role="status"
      aria-label="Loading"
    />
  );
};

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Skeleton: React.FC<SkeletonProps> = ({ className, ...props }) => {
  return (
    <div
      className={twMerge(clsx(styles.skeleton, className))}
      {...props}
    />
  );
};
