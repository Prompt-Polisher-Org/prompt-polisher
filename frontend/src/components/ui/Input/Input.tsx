import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import styles from './Input.module.scss';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement> {
  label?: string;
  error?: string;
  multiline?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, InputProps>(
  ({ className, label, error, multiline, ...props }, ref) => {
    const Component = multiline ? 'textarea' : 'input';
    
    return (
      <div className={styles.inputWrapper}>
        {label && <label className={styles.label}>{label}</label>}
        <Component
          ref={ref as any}
          className={twMerge(
            clsx(styles.input, multiline && styles.textarea, error && styles.hasError, className)
          )}
          {...(props as any)}
        />
        {error && <span className={styles.error}>{error}</span>}
      </div>
    );
  }
);

Input.displayName = 'Input';
