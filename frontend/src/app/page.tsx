'use client';

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  ArrowDown,
  ArrowRight,
  Check,
  FileText,
  History,
  MessageSquareText,
  Sparkles,
  WandSparkles,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import styles from './page.module.scss';

const features = [
  {
    icon: <WandSparkles size={20} aria-hidden="true" />,
    eyebrow: '01 / Refine',
    title: 'Give a rough idea a clear shape',
    description:
      'Turn a short request into a more specific prompt with context, constraints, and a useful output format.',
  },
  {
    icon: <MessageSquareText size={20} aria-hidden="true" />,
    eyebrow: '02 / Iterate',
    title: 'Keep working in one conversation',
    description:
      'Create separate chat sessions, continue where you left off, and keep earlier prompt work available.',
  },
  {
    icon: <History size={20} aria-hidden="true" />,
    eyebrow: '03 / Reuse',
    title: 'Build a library of better prompts',
    description:
      'Review previous sessions and refine the same idea again as your task or requirements change.',
  },
];

function FeatureCard({
  feature,
  index,
}: {
  feature: (typeof features)[number];
  index: number;
}) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      ref.current?.classList.add(styles.visible);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          const element = entry.target as HTMLElement;
          element.style.animationDelay = `${index * 0.08}s`;
          element.classList.add(styles.visible);
          observer.unobserve(element);
        }
      },
      { threshold: 0.15 },
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [index]);

  return (
    <article ref={ref} className={styles.featureCard}>
      <div className={styles.featureTopline}>
        <span className={styles.featureIcon}>{feature.icon}</span>
        <span className={styles.featureEyebrow}>{feature.eyebrow}</span>
      </div>
      <h3>{feature.title}</h3>
      <p>{feature.description}</p>
    </article>
  );
}

export default function Home() {
  return (
    <div className={styles.page}>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <header className={styles.header}>
        <nav className={styles.navbar} aria-label="Main navigation">
          <Link href="/" className={styles.brand} aria-label="Prompt Polisher home">
            <span className={styles.logoMark} aria-hidden="true">
              <WandSparkles size={17} />
            </span>
            <span>prompt<span className={styles.brandAccent}>polisher</span></span>
          </Link>
          <div className={styles.navActions}>
            <Link href="#how-it-works" className={styles.navLink}>How it works</Link>
            <ThemeToggle />
            <Link href="/login" className={styles.signIn}>Sign in</Link>
            <Link href="/register" className={styles.navCta}>Open workspace <ArrowRight size={15} /></Link>
          </div>
        </nav>
      </header>

      <main id="main-content">
        <section className={styles.hero} aria-labelledby="hero-heading">
          <div className={styles.heroGlow} aria-hidden="true" />
          <div className={styles.heroInner}>
            <div className={styles.heroCopy}>
              <div className={styles.eyebrow}><span className={styles.statusDot} /> A workspace for clearer AI instructions</div>
              <h1 id="hero-heading">Make your next prompt <span>work harder.</span></h1>
              <p className={styles.heroSubtitle}>
                Start with the idea you have. Shape it into a clear, structured prompt you can use, edit, and come back to.
              </p>
              <div className={styles.heroActions}>
                <Link href="/register" className={styles.primaryButton}>Try Prompt Polisher <ArrowRight size={17} /></Link>
                <Link href="#how-it-works" className={styles.secondaryButton}><ArrowDown size={16} /> See how it works</Link>
              </div>
              <div className={styles.heroNote}>
                <span className={styles.noteCheck}><Check size={13} /></span>
                Designed for drafting, refining, and revisiting prompts
              </div>
            </div>

            <div className={styles.previewWrap} aria-label="Example prompt refinement preview">
              <div className={styles.previewGlow} aria-hidden="true" />
              <div className={styles.previewCard}>
                <div className={styles.previewHeader}>
                  <div className={styles.windowDots} aria-hidden="true"><i /><i /><i /></div>
                  <span className={styles.previewLabel}><Sparkles size={13} /> WORKSPACE PREVIEW</span>
                  <span className={styles.previewMenu} aria-hidden="true">•••</span>
                </div>
                <div className={styles.previewBody}>
                  <div className={styles.promptBlock}>
                    <div className={styles.blockLabel}><span className={styles.userMark}>Y</span> YOUR IDEA <span className={styles.exampleTag}>EXAMPLE</span></div>
                    <p>Help me plan a social media launch for my new coffee shop.</p>
                  </div>
                  <div className={styles.transformMark} aria-hidden="true"><ArrowDown size={15} /></div>
                  <div className={styles.resultBlock}>
                    <div className={styles.blockLabel}><span className={styles.aiMark}><Sparkles size={12} /></span> REFINED PROMPT <span className={styles.readyTag}>READY TO EDIT</span></div>
                    <p className={styles.resultText}>
                      <strong>Role</strong> Act as a local marketing strategist.<br /><br />
                      <strong>Task</strong> Create a 2-week launch plan for a neighborhood coffee shop.<br /><br />
                      <strong>Include</strong> Post ideas, sample captions, a schedule, and a modest-budget approach.
                    </p>
                  </div>
                  <div className={styles.previewFooter}>
                    <span><FileText size={14} /> Example only — edit the result to fit your needs</span>
                    <span className={styles.copyHint}>Clearer structure <Check size={13} /></span>
                  </div>
                </div>
              </div>
              <div className={styles.floatingNote}><span><Check size={13} /></span> More context, less guesswork</div>
            </div>
          </div>
          <div className={styles.heroFoot}>
            <span>IDEA</span><span className={styles.footLine} /><span>STRUCTURE</span><span className={styles.footLine} /><span>BETTER PROMPTS</span>
          </div>
        </section>

        <section className={styles.workflow} id="how-it-works" aria-labelledby="workflow-heading">
          <div className={styles.sectionIntro}>
            <span className={styles.sectionKicker}>A simpler prompt workflow</span>
            <h2 id="workflow-heading">From first thought to ready-to-use prompt.</h2>
            <p>Prompt Polisher gives your ideas a practical structure, then keeps your work easy to revisit.</p>
          </div>
          <div className={styles.featureGrid}>
            {features.map((feature, index) => <FeatureCard key={feature.eyebrow} feature={feature} index={index} />)}
          </div>
        </section>

        <section className={styles.bottomCta}>
          <div className={styles.ctaGlyph} aria-hidden="true"><WandSparkles size={23} /></div>
          <div>
            <p className={styles.sectionKicker}>Your next draft starts here</p>
            <h2>Bring an idea. Leave with a clearer prompt.</h2>
          </div>
          <Link href="/register" className={styles.primaryButton}>Get started <ArrowRight size={17} /></Link>
        </section>
      </main>

      <footer className={styles.footer}>
        <Link href="/" className={styles.brand}>
          <span className={styles.logoMark} aria-hidden="true"><WandSparkles size={15} /></span>
          <span>prompt<span className={styles.brandAccent}>polisher</span></span>
        </Link>
        <span>A project for more thoughtful AI prompts.</span>
        <span>© {new Date().getFullYear()} Prompt Polisher</span>
      </footer>
    </div>
  );
}
