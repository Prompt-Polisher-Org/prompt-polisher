'use client';

/**
 * Landing Page v2 — Final Version
 *
 * Sections:
 *  1. Navbar (logo + actions + ThemeToggle)
 *  2. Hero — animated gradient orb background, headline, CTA, stats
 *  3. Features — 6-card grid, scroll-triggered fade-in via IntersectionObserver
 *  4. Testimonials — 3 mock cards with avatar, stars, quote
 *  5. CTA — gradient-background call-to-action band
 *  6. Footer — 3-column links + copyright
 *
 * Accessibility:
 *  - Skip navigation link (#main-content)
 *  - All interactive elements have aria-labels or meaningful text
 *  - Color contrast meets WCAG 2.1 AA (verified against CSS vars)
 *  - IntersectionObserver honours prefers-reduced-motion
 */

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
import { Wand2, ArrowRight, Zap, Brain, Shield, BarChart2, GitBranch, Sparkles } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import styles from './page.module.scss';

/* ─── Data ─────────────────────────────────────────────────────────────── */

const features = [
  {
    icon: <Brain size={22} color="#818cf8" aria-hidden="true" />,
    iconBg: 'rgba(99,102,241,0.15)',
    title: 'RLHF-Tuned Model',
    description:
      'Our language model is fine-tuned with Reinforcement Learning from Human Feedback, so every suggestion is grounded in real-world quality signals.',
  },
  {
    icon: <Zap size={22} color="#f59e0b" aria-hidden="true" />,
    iconBg: 'rgba(245,158,11,0.15)',
    title: 'Instant Optimization',
    description:
      'Get polished prompts in under a second. Redis caching ensures repeat patterns are served instantly without hitting the inference engine.',
  },
  {
    icon: <GitBranch size={22} color="#10b981" aria-hidden="true" />,
    iconBg: 'rgba(16,185,129,0.15)',
    title: 'RAG Context Engine',
    description:
      'Our Retrieval-Augmented Generation pipeline pulls relevant best-practice examples from a curated Qdrant vector database to enrich your prompts.',
  },
  {
    icon: <BarChart2 size={22} color="#06b6d4" aria-hidden="true" />,
    iconBg: 'rgba(6,182,212,0.15)',
    title: 'Analytics Dashboard',
    description:
      'Track prompt quality, session trends, and feedback ratings over time with interactive Recharts visualizations.',
  },
  {
    icon: <Shield size={22} color="#a78bfa" aria-hidden="true" />,
    iconBg: 'rgba(167,139,250,0.15)',
    title: 'Enterprise Security',
    description:
      'JWT authentication with refresh tokens, hardened Pydantic schemas, rate limiting, and at-rest encryption for sensitive data.',
  },
  {
    icon: <Sparkles size={22} color="#ec4899" aria-hidden="true" />,
    iconBg: 'rgba(236,72,153,0.15)',
    title: 'Continuous Learning',
    description:
      'Every thumbs-up or thumbs-down you give trains the next model iteration via DPO, making Prompt Polisher smarter for everyone.',
  },
];

const testimonials = [
  {
    initials: 'AS',
    name: 'Aisha S.',
    role: 'ML Engineer at DataScale',
    quote:
      '"Prompt Polisher cut my prompt iteration time in half. The RAG context engine consistently pulls the exact best-practice examples I need."',
  },
  {
    initials: 'RK',
    name: 'Raj K.',
    role: 'Product Lead at NovaTech',
    quote:
      '"We integrated Prompt Polisher into our internal tooling and saw a 34% improvement in LLM output quality across the board within the first week."',
  },
  {
    initials: 'LP',
    name: 'Laura P.',
    role: 'AI Researcher',
    quote:
      '"The analytics dashboard gives me exactly the feedback loop I was missing. I can actually see how my prompt style evolves week over week."',
  },
];

/* ─── Feature Card with IntersectionObserver ────────────────────────────── */

function FeatureCard({
  feature,
  index,
}: {
  feature: (typeof features)[0];
  index: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Respect prefers-reduced-motion — skip animation
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) {
      ref.current?.classList.add(styles.visible);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target as HTMLElement;
            el.style.animationDelay = `${index * 0.08}s`;
            el.classList.add(styles.visible);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.15 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [index]);

  return (
    <div ref={ref} className={styles.featureCard} tabIndex={0}>
      <div
        className={styles.featureIcon}
        style={{ background: feature.iconBg }}
        aria-hidden="true"
      >
        {feature.icon}
      </div>
      <h3>{feature.title}</h3>
      <p>{feature.description}</p>
    </div>
  );
}

/* ─── Main Page ─────────────────────────────────────────────────────────── */

export default function Home() {
  return (
    <div className={styles.page}>
      {/* Skip Navigation — screen reader / keyboard shortcut */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header role="banner">
        <nav className={styles.navbar} aria-label="Main navigation">
          <Link href="/" className={styles.navLogo} aria-label="Prompt Polisher home">
            <span className={styles.logoMark} aria-hidden="true">
              <Wand2 size={16} color="white" />
            </span>
            Prompt Polisher
          </Link>

          <div className={styles.navActions}>
            <Link href="/login" className={styles.navLink}>
              Sign in
            </Link>
            <ThemeToggle />
            <Link href="/register" className={styles.btnPrimary} style={{ padding: '0.5rem 1.25rem', fontSize: '0.9375rem' }}>
              Get Started
              <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <main id="main-content">
        <section className={styles.heroSection} aria-labelledby="hero-heading">
          <div className={styles.heroGrid} aria-hidden="true" />

          <div className={styles.heroContent}>
            <div className={styles.heroBadge} aria-label="Powered by RLHF and RAG">
              <Sparkles size={13} aria-hidden="true" />
              RLHF + RAG · Production Ready
            </div>

            <h1 id="hero-heading" className={styles.heroTitle}>
              Your AI Prompts,{' '}
              <span className={styles.gradient}>Perfected.</span>
            </h1>

            <p className={styles.heroSubtitle}>
              Transform rough ideas into expertly crafted instructions.
              Our RLHF-tuned model and RAG pipeline optimize your prompts
              for maximum AI performance — in under a second.
            </p>

            <div className={styles.heroCta}>
              <Link href="/register" className={styles.btnPrimary} id="hero-cta-primary">
                Start Polishing Free
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link href="/login" className={styles.btnGhost} id="hero-cta-secondary">
                Sign In
              </Link>
            </div>

            <div className={styles.heroStats} role="list" aria-label="Platform statistics">
              <div className={styles.statItem} role="listitem">
                <strong>10k+</strong>
                <span>Prompts Polished</span>
              </div>
              <div className={styles.statItem} role="listitem">
                <strong>87%</strong>
                <span>Avg Quality Score</span>
              </div>
              <div className={styles.statItem} role="listitem">
                <strong>&lt;1s</strong>
                <span>Response Time</span>
              </div>
              <div className={styles.statItem} role="listitem">
                <strong>WCAG AA</strong>
                <span>Accessibility</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────────────── */}
        <section aria-labelledby="features-heading">
          <div className={styles.section}>
            <div className={styles.sectionLabel}>
              <p aria-hidden="true">Why Prompt Polisher</p>
              <h2 id="features-heading">Everything you need to craft perfect prompts</h2>
              <p className={styles.subtext}>
                Built with a production-grade ML pipeline, enterprise security,
                and a developer-first experience.
              </p>
            </div>

            <div
              className={styles.featureGrid}
              role="list"
              aria-label="Platform features"
            >
              {features.map((feature, i) => (
                <div key={feature.title} role="listitem">
                  <FeatureCard feature={feature} index={i} />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Testimonials ─────────────────────────────────────────────── */}
        <section
          className={styles.testimonialsSection}
          aria-labelledby="testimonials-heading"
        >
          <div className={styles.testimonialsInner}>
            <div className={styles.sectionLabel}>
              <p aria-hidden="true">Testimonials</p>
              <h2 id="testimonials-heading">Loved by AI practitioners</h2>
              <p className={styles.subtext}>
                Here's what engineers and researchers say about Prompt Polisher.
              </p>
            </div>

            <ul className={styles.testimonialsGrid} aria-label="Customer testimonials">
              {testimonials.map((t) => (
                <li key={t.name} className={styles.testimonialCard}>
                  <div className={styles.stars} aria-label="5 stars">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <span key={i} aria-hidden="true">★</span>
                    ))}
                  </div>
                  <p className={styles.testimonialText}>{t.quote}</p>
                  <div className={styles.testimonialAuthor}>
                    <div
                      className={styles.avatar}
                      aria-hidden="true"
                    >
                      {t.initials}
                    </div>
                    <div className={styles.authorInfo}>
                      <strong>{t.name}</strong>
                      <span>{t.role}</span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ── CTA ──────────────────────────────────────────────────────── */}
        <section className={styles.ctaSection} aria-labelledby="cta-heading">
          <div className={styles.ctaInner}>
            <h2 id="cta-heading">
              Ready to polish your prompts?
            </h2>
            <p>
              Join thousands of AI practitioners who use Prompt Polisher to get
              better results from their LLMs — for free.
            </p>
            <div className={styles.ctaButtons}>
              <Link href="/register" className={styles.btnPrimary} id="cta-signup">
                Create Free Account
                <ArrowRight size={18} aria-hidden="true" />
              </Link>
              <Link href="/login" className={styles.btnGhost} id="cta-signin">
                Sign In
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className={styles.footer} role="contentinfo">
        <div className={styles.footerInner}>
          <div className={styles.footerTop}>
            <div className={styles.footerBrand}>
              <Link href="/" className={styles.navLogo} aria-label="Prompt Polisher home">
                <span className={styles.logoMark} aria-hidden="true">
                  <Wand2 size={14} color="white" />
                </span>
                Prompt Polisher
              </Link>
              <p>
                AI-powered prompt optimization using RLHF, RAG, and a
                production-grade multi-node architecture.
              </p>
            </div>

            <nav className={styles.footerCol} aria-label="Product links">
              <h4>Product</h4>
              <ul>
                <li><Link href="/register">Get Started</Link></li>
                <li><Link href="/dashboard">Dashboard</Link></li>
                <li><Link href="/dashboard/analytics">Analytics</Link></li>
                <li><Link href="/dashboard/preferences">Preferences</Link></li>
              </ul>
            </nav>

            <nav className={styles.footerCol} aria-label="Company links">
              <h4>Company</h4>
              <ul>
                <li><a href="#features">About</a></li>
                <li><a href="#testimonials">Testimonials</a></li>
                <li><a href="https://github.com" rel="noopener noreferrer" target="_blank">GitHub</a></li>
              </ul>
            </nav>

            <nav className={styles.footerCol} aria-label="Support links">
              <h4>Support</h4>
              <ul>
                <li><a href="mailto:support@promptpolisher.ai">Contact</a></li>
                <li><a href="#privacy">Privacy Policy</a></li>
                <li><a href="#terms">Terms of Service</a></li>
              </ul>
            </nav>
          </div>

          <div className={styles.footerBottom}>
            <p>© {new Date().getFullYear()} Prompt Polisher. All rights reserved.</p>
            <div className={styles.footerBottomLinks}>
              <a href="#privacy">Privacy</a>
              <a href="#terms">Terms</a>
              <a href="#cookies">Cookies</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
