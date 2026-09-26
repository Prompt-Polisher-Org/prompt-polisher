'use client';

/**
 * PromptTemplates.tsx
 * Week 7-8 / Enhanced Chat UI - Prompt Templates / Quick-Starts
 * [x] Template cards for common use cases (6 domains × 3 templates = 18 cards)
 * [x] Click to pre-fill prompt input
 * [x] Animated card hover effects
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Code2, PenLine, Megaphone, GraduationCap, Lightbulb, FlaskConical,
} from 'lucide-react';

export interface PromptTemplate {
  id: string;
  domain: string;
  title: string;
  description: string;
  prompt: string;
  icon: React.ReactNode;
  gradient: string;
}

const TEMPLATES: PromptTemplate[] = [
  // ── Coding ──────────────────────────────────────────────────────────────
  {
    id: 'code-review',
    domain: 'coding',
    title: 'Code Review',
    description: 'Get detailed feedback on your code quality and security',
    prompt:
      'Please review the following code for bugs, performance issues, and security vulnerabilities. Provide specific, actionable suggestions for each finding:\n\n```\n[PASTE YOUR CODE HERE]\n```',
    icon: <Code2 size={18} />,
    gradient: 'from-cyan-500/20 to-blue-500/20',
  },
  {
    id: 'debug-help',
    domain: 'coding',
    title: 'Debug This Error',
    description: 'Get step-by-step help diagnosing an error or bug',
    prompt:
      "I'm getting this error and I'm not sure why:\n\nError: [PASTE ERROR MESSAGE]\n\nHere's the relevant code:\n```\n[PASTE CODE]\n```\n\nPlease explain the root cause and provide a fix.",
    icon: <Code2 size={18} />,
    gradient: 'from-cyan-500/20 to-blue-500/20',
  },
  {
    id: 'algorithm-design',
    domain: 'coding',
    title: 'Design an Algorithm',
    description: 'Get time/space complexity analysis and implementation',
    prompt:
      'Design an efficient algorithm for the following problem. Include time complexity, space complexity, and a Python implementation with test cases:\n\nProblem: [DESCRIBE YOUR PROBLEM]',
    icon: <Code2 size={18} />,
    gradient: 'from-cyan-500/20 to-blue-500/20',
  },

  // ── Writing ──────────────────────────────────────────────────────────────
  {
    id: 'blog-post',
    domain: 'writing',
    title: 'Write a Blog Post',
    description: 'Generate a structured, SEO-ready blog post on any topic',
    prompt:
      'Write an engaging 800-word blog post about [TOPIC] for [TARGET AUDIENCE]. Include a compelling headline, 3–4 main sections with subheadings, and a strong call-to-action at the end. Tone: [professional/casual/academic].',
    icon: <PenLine size={18} />,
    gradient: 'from-violet-500/20 to-purple-500/20',
  },
  {
    id: 'cover-letter',
    domain: 'writing',
    title: 'Cover Letter',
    description: 'Craft a personalised, compelling cover letter',
    prompt:
      'Write a compelling cover letter for a [JOB TITLE] position at [COMPANY NAME]. My top 3 relevant skills are: [SKILL 1], [SKILL 2], [SKILL 3]. Keep it under 300 words with a professional yet personal tone.',
    icon: <PenLine size={18} />,
    gradient: 'from-violet-500/20 to-purple-500/20',
  },
  {
    id: 'email-rewrite',
    domain: 'writing',
    title: 'Rewrite an Email',
    description: 'Make your email clearer, more professional, or more persuasive',
    prompt:
      'Rewrite the following email to be more [clear/professional/persuasive]. Improve the subject line, make the ask crystal clear, and keep it under 150 words:\n\n[PASTE YOUR EMAIL]',
    icon: <PenLine size={18} />,
    gradient: 'from-violet-500/20 to-purple-500/20',
  },

  // ── Marketing ────────────────────────────────────────────────────────────
  {
    id: 'ad-copy',
    domain: 'marketing',
    title: 'Ad Copy',
    description: 'Generate high-converting ad copy for any platform',
    prompt:
      'Write 3 variations of Facebook ad copy for [PRODUCT/SERVICE]. Target audience: [DESCRIBE AUDIENCE]. Each variation should use a different angle: (1) emotional appeal, (2) logical/data-driven, (3) social proof. Include a CTA for each.',
    icon: <Megaphone size={18} />,
    gradient: 'from-orange-500/20 to-amber-500/20',
  },
  {
    id: 'product-description',
    domain: 'marketing',
    title: 'Product Description',
    description: 'Write a persuasive, benefit-focused product description',
    prompt:
      'Write a persuasive product description for [PRODUCT NAME]. Target buyer: [BUYER PERSONA]. Focus on benefits (not features), include an emotional hook, and end with a clear call-to-action. Length: 100–150 words. Tone: [TONE].',
    icon: <Megaphone size={18} />,
    gradient: 'from-orange-500/20 to-amber-500/20',
  },
  {
    id: 'social-post',
    domain: 'marketing',
    title: 'LinkedIn Post',
    description: 'Write a high-engagement LinkedIn post on any topic',
    prompt:
      'Write a high-engagement LinkedIn post about [TOPIC] from the perspective of [YOUR ROLE]. Open with a pattern-interrupt first line. Share a specific insight or story. End with a thought-provoking question. Max 200 words.',
    icon: <Megaphone size={18} />,
    gradient: 'from-orange-500/20 to-amber-500/20',
  },

  // ── Education ────────────────────────────────────────────────────────────
  {
    id: 'explain-concept',
    domain: 'education',
    title: 'Explain Simply',
    description: 'Get a clear, jargon-free explanation of any concept',
    prompt:
      'Explain [COMPLEX CONCEPT] in plain English that a [BACKGROUND, e.g. high-schooler / non-technical manager] can understand. Use an analogy from everyday life and include 2 concrete examples.',
    icon: <GraduationCap size={18} />,
    gradient: 'from-emerald-500/20 to-teal-500/20',
  },
  {
    id: 'quiz-generator',
    domain: 'education',
    title: 'Create a Quiz',
    description: 'Generate quiz questions with answers for any topic',
    prompt:
      'Create 10 quiz questions about [TOPIC] for [LEVEL: beginner/intermediate/advanced] learners. Include: 5 multiple-choice (4 options each), 3 true/false, and 2 short-answer questions. Provide the answer key at the end.',
    icon: <GraduationCap size={18} />,
    gradient: 'from-emerald-500/20 to-teal-500/20',
  },
  {
    id: 'study-guide',
    domain: 'education',
    title: 'Study Guide',
    description: 'Create a comprehensive study guide from any topic',
    prompt:
      'Create a comprehensive study guide for [TOPIC] covering [EXAM OR PURPOSE]. Include: key concepts with definitions, important formulas or rules, 5 practice questions with answers, and 3 common mistakes to avoid.',
    icon: <GraduationCap size={18} />,
    gradient: 'from-emerald-500/20 to-teal-500/20',
  },

  // ── Creative ─────────────────────────────────────────────────────────────
  {
    id: 'story-opening',
    domain: 'creative',
    title: 'Story Opening',
    description: 'Start your story with a captivating hook',
    prompt:
      'Write the opening 200 words of a [GENRE] story set in [SETTING]. The protagonist is [BRIEF DESCRIPTION]. Start in-scene (in medias res), use vivid sensory detail, and end the scene at a moment of tension. Show, don\'t tell.',
    icon: <Lightbulb size={18} />,
    gradient: 'from-pink-500/20 to-rose-500/20',
  },
  {
    id: 'character-development',
    domain: 'creative',
    title: 'Develop a Character',
    description: 'Build a complex, believable character with depth',
    prompt:
      'Develop a complex character for my [GENRE] story. Name: [NAME]. Role: [PROTAGONIST/ANTAGONIST]. Please define: their core wound and how it drives their behaviour, one key contradiction that makes them interesting, their want vs their true need, and their distinctive voice or speech patterns.',
    icon: <Lightbulb size={18} />,
    gradient: 'from-pink-500/20 to-rose-500/20',
  },
  {
    id: 'creative-brainstorm',
    domain: 'creative',
    title: 'Brainstorm Ideas',
    description: 'Generate a diverse range of creative ideas fast',
    prompt:
      'Generate 20 creative ideas for [YOUR CREATIVE CHALLENGE]. Do not filter — include wild, impractical ideas alongside sensible ones. Then identify the 3 most promising ideas and explain why each could work well.',
    icon: <Lightbulb size={18} />,
    gradient: 'from-pink-500/20 to-rose-500/20',
  },

  // ── Research ─────────────────────────────────────────────────────────────
  {
    id: 'literature-review',
    domain: 'research',
    title: 'Literature Review',
    description: 'Synthesise research on any topic into a structured overview',
    prompt:
      'Write a structured literature review on [TOPIC]. Synthesise the key themes and findings (do not summarise paper-by-paper), identify areas of scholarly consensus and debate, and conclude with 2–3 open research questions. Audience: [AUDIENCE LEVEL].',
    icon: <FlaskConical size={18} />,
    gradient: 'from-indigo-500/20 to-blue-500/20',
  },
  {
    id: 'data-analysis',
    domain: 'research',
    title: 'Analyse Data',
    description: 'Get a structured plan or interpretation for your dataset',
    prompt:
      'I have a dataset containing [DESCRIBE YOUR DATA]. I want to answer this question: [YOUR RESEARCH QUESTION]. Please provide: (1) the appropriate statistical test(s) to use and why, (2) the analysis steps in order, (3) how to interpret the results for a non-technical audience.',
    icon: <FlaskConical size={18} />,
    gradient: 'from-indigo-500/20 to-blue-500/20',
  },
  {
    id: 'research-summary',
    domain: 'research',
    title: 'Summarise Research',
    description: 'Extract key insights from any research paper or report',
    prompt:
      'Summarise the following research document for a [AUDIENCE] audience. Extract: (1) the core research question, (2) methodology used, (3) 3 key findings with their significance, (4) main limitations, (5) practical takeaways. Keep it under 400 words.\n\n[PASTE ABSTRACT OR KEY SECTIONS]',
    icon: <FlaskConical size={18} />,
    gradient: 'from-indigo-500/20 to-blue-500/20',
  },
];

interface PromptTemplatesProps {
  onSelectTemplate: (prompt: string) => void;
}

const DOMAIN_LABELS: Record<string, string> = {
  coding: 'Coding',
  writing: 'Writing',
  marketing: 'Marketing',
  education: 'Education',
  creative: 'Creative',
  research: 'Research',
};

export function PromptTemplates({ onSelectTemplate }: PromptTemplatesProps) {
  const [activeFilter, setActiveFilter] = useState<string>('all');

  const domains = ['all', ...Object.keys(DOMAIN_LABELS)];
  const filtered = activeFilter === 'all'
    ? TEMPLATES
    : TEMPLATES.filter(t => t.domain === activeFilter);

  return (
    <div className="w-full">
      {/* Domain filter tabs */}
      <div className="flex flex-wrap gap-2 mb-5">
        {domains.map(domain => (
          <button
            key={domain}
            onClick={() => setActiveFilter(domain)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 border ${
              activeFilter === domain
                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/20'
                : 'bg-slate-800/60 text-slate-400 border-slate-700/50 hover:text-white hover:bg-slate-800'
            }`}
          >
            {domain === 'all' ? 'All Templates' : DOMAIN_LABELS[domain]}
          </button>
        ))}
      </div>

      {/* Template cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((template, i) => (
          <motion.button
            key={template.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => onSelectTemplate(template.prompt)}
            className={`group relative text-left p-4 rounded-xl border border-slate-700/50
                        bg-gradient-to-br ${template.gradient} bg-slate-800/60
                        hover:border-slate-600 hover:scale-[1.02] hover:shadow-lg hover:shadow-slate-900/40
                        transition-all duration-200 cursor-pointer`}
          >
            {/* Icon + Domain badge */}
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-indigo-400 group-hover:text-indigo-300 transition-colors">
                {template.icon}
              </span>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                {DOMAIN_LABELS[template.domain]}
              </span>
            </div>

            {/* Title */}
            <h3 className="text-sm font-semibold text-slate-200 mb-1 group-hover:text-white transition-colors">
              {template.title}
            </h3>

            {/* Description */}
            <p className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
              {template.description}
            </p>

            {/* Hover CTA */}
            <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-[10px] text-indigo-400 font-medium">Use template →</span>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
