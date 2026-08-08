'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import styles from './Register.module.scss';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0); // 0-4
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Simple password strength evaluator
  useEffect(() => {
    const pwd = formData.password;
    let strength = 0;
    if (pwd.length > 0) strength += 1;
    if (pwd.length >= 8) strength += 1;
    if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) strength += 1;
    if (/[0-9]/.test(pwd) || /[^A-Za-z0-9]/.test(pwd)) strength += 1;
    setPasswordStrength(strength);
  }, [formData.password]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.id]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (passwordStrength < 2) {
      setError('Password is too weak. Please use at least 8 characters with letters and numbers.');
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/auth/register', {
        email: formData.email,
        password: formData.password,
        full_name: formData.name
      });
      
      // Show success animation
      setIsSuccess(true);
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('An account with this email already exists');
      } else if (err.response?.status === 422) {
        setError('Invalid input data provided');
      } else {
        setError('Registration failed. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getStrengthClass = (level: number) => {
    if (passwordStrength < level) return '';
    if (passwordStrength === 1) return styles.weak;
    if (passwordStrength === 2) return styles.fair;
    if (passwordStrength === 3) return styles.good;
    return styles.strong;
  };

  return (
    <div className={styles.container}>
      <AnimatePresence mode="wait">
        {!isSuccess ? (
          <motion.div 
            key="form"
            className={styles.card}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.5 }}
          >
            <div className={styles.header}>
              <h1>Create an account</h1>
              <p>Start optimizing your AI prompts today</p>
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
                <label htmlFor="name">Full Name</label>
                <input 
                  id="name"
                  type="text" 
                  placeholder="Jane Doe" 
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="email">Email address</label>
                <input 
                  id="email"
                  type="email" 
                  placeholder="you@example.com" 
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="password">Password</label>
                <input 
                  id="password"
                  type="password" 
                  placeholder="Create a strong password" 
                  value={formData.password}
                  onChange={handleChange}
                  required
                />
                <div className={styles.passwordStrength}>
                  <div className={`${styles.bar} ${getStrengthClass(1) ? styles.active : ''} ${getStrengthClass(1)}`} />
                  <div className={`${styles.bar} ${getStrengthClass(2) ? styles.active : ''} ${getStrengthClass(2)}`} />
                  <div className={`${styles.bar} ${getStrengthClass(3) ? styles.active : ''} ${getStrengthClass(3)}`} />
                  <div className={`${styles.bar} ${getStrengthClass(4) ? styles.active : ''} ${getStrengthClass(4)}`} />
                </div>
              </div>

              <div className={styles.inputGroup}>
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input 
                  id="confirmPassword"
                  type="password" 
                  placeholder="Confirm your password" 
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className={styles.termsGroup}>
                <input 
                  type="checkbox" 
                  id="terms" 
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  required
                />
                <label htmlFor="terms">
                  I agree to the <Link href="/terms">Terms of Service</Link> and <Link href="/privacy">Privacy Policy</Link>
                </label>
              </div>

              <button 
                type="submit" 
                className={styles.submitBtn}
                disabled={isLoading || !acceptedTerms || !formData.email || !formData.password}
              >
                {isLoading ? <Loader2 className="animate-spin mx-auto" size={20} /> : 'Create Account'}
              </button>
            </form>

            <div className={styles.footer}>
              Already have an account? <Link href="/login">Sign in</Link>
            </div>
          </motion.div>
        ) : (
          <motion.div 
            key="success"
            className={styles.card}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, type: 'spring' }}
          >
            <div className={styles.successState}>
              <motion.div 
                className={styles.checkIcon}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
              >
                <Check />
              </motion.div>
              <h2>Registration Successful!</h2>
              <p>Your account has been created. Please log in to set up your preferences.</p>
              <Link href="/login" className={styles.continueBtn}>
                Proceed to Login
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
