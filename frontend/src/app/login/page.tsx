'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Github, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import styles from './Login.module.scss';

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // POST /api/v1/auth/login expects email and password
      const response = await api.post('/auth/login', { email, password });
      
      // Store tokens and update state
      login({
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
      });

      // Redirect to dashboard (or onboarding if needed)
      router.push('/dashboard');
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid email or password');
      } else if (err.response?.status === 422) {
        setError('Please enter a valid email address');
      } else {
        setError('Something went wrong. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <motion.div 
        className={styles.card}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className={styles.header}>
          <h1>Welcome back</h1>
          <p>Sign in to your Prompt Polisher account</p>
        </div>

        {error && (
          <motion.div 
            className={styles.error}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            {error}
          </motion.div>
        )}

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <label htmlFor="email">Email address</label>
            <input 
              id="email"
              type="email" 
              placeholder="you@example.com" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">Password</label>
            <input 
              id="password"
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Link href="/forgot-password" className={styles.forgotPassword}>
            Forgot password?
          </Link>

          <button 
            type="submit" 
            className={styles.submitBtn}
            disabled={isLoading || !email || !password}
          >
            {isLoading ? <Loader2 className="animate-spin mx-auto" size={20} /> : 'Sign in'}
          </button>
        </form>

        <div className={styles.divider}>
          <span>Or continue with</span>
        </div>

        <div className={styles.socialButtons}>
          <button className={styles.socialBtn} type="button" onClick={() => alert('Google OAuth not implemented yet')}>
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google
          </button>
          <button className={styles.socialBtn} type="button" onClick={() => alert('GitHub OAuth not implemented yet')}>
            <Github />
            GitHub
          </button>
        </div>

        <div className={styles.footer}>
          Don't have an account? <Link href="/register">Sign up</Link>
        </div>
      </motion.div>
    </div>
  );
}
