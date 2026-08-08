'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Check, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import styles from './Onboarding.module.scss';

// Preference Options Data
const TONE_OPTIONS = [
  { id: 'professional', title: 'Professional', desc: 'Formal, polite, and objective. Best for business.' },
  { id: 'casual', title: 'Casual', desc: 'Relaxed and conversational. Best for social media.' },
  { id: 'academic', title: 'Academic', desc: 'Rigorous and scholarly. Best for research.' },
  { id: 'creative', title: 'Creative', desc: 'Imaginative and engaging. Best for storytelling.' },
];

const VERBOSITY_OPTIONS = [
  { id: 'concise', title: 'Concise', desc: 'Short and to the point. No fluff.' },
  { id: 'balanced', title: 'Balanced', desc: 'Just enough detail without being overwhelming.' },
  { id: 'detailed', title: 'Detailed', desc: 'Comprehensive explanations with examples.' },
];

const MODEL_OPTIONS = [
  { id: 'gpt-4', title: 'GPT-4', desc: 'OpenAI\'s most capable model.' },
  { id: 'claude', title: 'Claude 3', desc: 'Anthropic\'s highly nuanced model.' },
  { id: 'gemini', title: 'Gemini Pro', desc: 'Google\'s multimodal AI.' },
  { id: 'general', title: 'General / Any', desc: 'Works well across all modern LLMs.' },
];

const DOMAIN_OPTIONS = [
  { id: 'coding', title: 'Software Engineering', desc: 'Code generation, debugging, architecture.' },
  { id: 'writing', title: 'Content Writing', desc: 'Blog posts, copywriting, essays.' },
  { id: 'marketing', title: 'Marketing', desc: 'SEO, campaigns, ad copy.' },
  { id: 'general', title: 'General Purpose', desc: 'Everyday tasks and varied requests.' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const totalSteps = 5;

  const [preferences, setPreferences] = useState({
    tone: '',
    verbosity: '',
    target_model: '',
    domain: '',
    custom_instructions: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const updatePreference = (key: string, value: string) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const handleNext = () => {
    if (step < totalSteps) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      await api.put('/users/me/preferences', preferences);
      router.push('/dashboard');
    } catch (err) {
      console.error(err);
      setError('Failed to save preferences. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const isStepValid = () => {
    switch (step) {
      case 1: return !!preferences.tone;
      case 2: return !!preferences.verbosity;
      case 3: return !!preferences.target_model;
      case 4: return !!preferences.domain;
      case 5: return true; // Custom instructions are optional
      default: return false;
    }
  };

  // Animation variants
  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 50 : -50,
      opacity: 0
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      zIndex: 0,
      x: direction < 0 ? 50 : -50,
      opacity: 0
    })
  };

  const renderOptions = (options: any[], key: keyof typeof preferences) => (
    <div className={styles.optionsGrid}>
      {options.map((opt) => (
        <div 
          key={opt.id}
          className={`${styles.optionCard} ${preferences[key] === opt.id ? styles.selected : ''}`}
          onClick={() => updatePreference(key, opt.id)}
        >
          <h3>{opt.title}</h3>
          <p>{opt.desc}</p>
        </div>
      ))}
    </div>
  );

  return (
    <div className={styles.container}>
      <div className={styles.wizardCard}>
        <div className={styles.header}>
          <h1>Customize your experience</h1>
          <p>Let's tailor Prompt Polisher to your needs.</p>
        </div>

        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div 
              className={styles.progressFill} 
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
          <div className={styles.stepIndicator}>
            <span>Step {step} of {totalSteps}</span>
            <span>
              {step === 1 && 'Tone'}
              {step === 2 && 'Verbosity'}
              {step === 3 && 'Target Model'}
              {step === 4 && 'Domain'}
              {step === 5 && 'Custom Instructions'}
            </span>
          </div>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.content}>
          <AnimatePresence mode="wait" custom={1}>
            {step === 1 && (
              <motion.div
                key="step1"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <h2 className={styles.stepTitle}>How should your prompts sound?</h2>
                {renderOptions(TONE_OPTIONS, 'tone')}
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <h2 className={styles.stepTitle}>How detailed should the output be?</h2>
                {renderOptions(VERBOSITY_OPTIONS, 'verbosity')}
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <h2 className={styles.stepTitle}>Which AI model do you use most?</h2>
                {renderOptions(MODEL_OPTIONS, 'target_model')}
              </motion.div>
            )}

            {step === 4 && (
              <motion.div
                key="step4"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <h2 className={styles.stepTitle}>What is your primary use case?</h2>
                {renderOptions(DOMAIN_OPTIONS, 'domain')}
              </motion.div>
            )}

            {step === 5 && (
              <motion.div
                key="step5"
                custom={1}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.3 }}
              >
                <h2 className={styles.stepTitle}>Any custom instructions? (Optional)</h2>
                <div className={styles.textareaContainer}>
                  <textarea
                    placeholder="E.g., Always use British English spelling. Never use emojis. Prefer bullet points over paragraphs."
                    value={preferences.custom_instructions}
                    onChange={(e) => updatePreference('custom_instructions', e.target.value)}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className={styles.footer}>
          <button 
            className={`${styles.btn} ${styles.btnSecondary}`}
            onClick={handleBack}
            disabled={step === 1 || isLoading}
          >
            <ChevronLeft size={18} />
            Back
          </button>
          
          {step < totalSteps ? (
            <button 
              className={`${styles.btn} ${styles.btnPrimary}`}
              onClick={handleNext}
              disabled={!isStepValid()}
            >
              Next
              <ChevronRight size={18} />
            </button>
          ) : (
            <button 
              className={`${styles.btn} ${styles.btnPrimary}`}
              onClick={handleSubmit}
              disabled={isLoading}
            >
              {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Check size={18} />}
              {isLoading ? 'Saving...' : 'Finish Setup'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
