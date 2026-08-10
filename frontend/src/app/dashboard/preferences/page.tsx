'use client';

/**
 * dashboard/preferences/page.tsx — Preferences Panel
 * Week 7-8 / Enhanced Chat UI
 * [x] View current preferences
 * [x] Edit preferences inline
 * [x] Preview: "Your preferences will make prompts like..."
 * [x] Save with success feedback + error handling
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Loader2, Wand2, ChevronDown, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

// ── Types ─────────────────────────────────────────────────────────────────────
interface Preferences {
  tone: string;
  verbosity: string;
  target_model: string;
  domain: string;
  custom_instructions: string;
}

const DEFAULT_PREFS: Preferences = {
  tone: 'professional',
  verbosity: 'balanced',
  target_model: 'General',
  domain: 'general',
  custom_instructions: '',
};

// ── Option definitions ────────────────────────────────────────────────────────
const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional', desc: 'Clear, formal, business-ready' },
  { value: 'casual', label: 'Casual', desc: 'Conversational and relaxed' },
  { value: 'academic', label: 'Academic', desc: 'Scholarly and citation-aware' },
  { value: 'creative', label: 'Creative', desc: 'Imaginative and expressive' },
];

const VERBOSITY_OPTIONS = [
  { value: 'concise', label: 'Concise', desc: 'Short, direct, no padding' },
  { value: 'balanced', label: 'Balanced', desc: 'Complete but not verbose' },
  { value: 'detailed', label: 'Detailed', desc: 'Thorough, step-by-step' },
];

const MODEL_OPTIONS = [
  { value: 'General', label: 'General', desc: 'Works with any AI model' },
  { value: 'GPT-4', label: 'GPT-4', desc: 'Optimised for OpenAI GPT-4' },
  { value: 'Claude', label: 'Claude', desc: 'Optimised for Anthropic Claude' },
  { value: 'Gemini', label: 'Gemini', desc: 'Optimised for Google Gemini' },
];

const DOMAIN_OPTIONS = [
  { value: 'general', label: 'General', icon: '🌐' },
  { value: 'coding', label: 'Coding', icon: '💻' },
  { value: 'writing', label: 'Writing', icon: '✍️' },
  { value: 'marketing', label: 'Marketing', icon: '📣' },
];

// ── Sub-components ────────────────────────────────────────────────────────────
function OptionCard({
  value,
  label,
  desc,
  selected,
  onClick,
}: {
  value: string;
  label: string;
  desc?: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex flex-col items-start text-left p-3 rounded-xl border transition-all duration-150 ${
        selected
          ? 'bg-indigo-600/15 border-indigo-500/60 shadow-md shadow-indigo-500/10'
          : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600 hover:bg-slate-800'
      }`}
    >
      <span className={`text-sm font-medium ${selected ? 'text-indigo-300' : 'text-slate-200'}`}>
        {label}
      </span>
      {desc && (
        <span className="text-xs text-slate-500 mt-0.5 leading-snug">{desc}</span>
      )}
      {selected && (
        <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-indigo-500 flex items-center justify-center">
          <Check size={10} className="text-white" strokeWidth={3} />
        </div>
      )}
    </button>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
      {children}
    </h2>
  );
}

// ── Preview component ─────────────────────────────────────────────────────────
function PreviewPane({ prefs }: { prefs: Preferences }) {
  const previewText = `You will receive prompts that are:\n• Written in a ${prefs.tone} tone\n• ${prefs.verbosity === 'concise' ? 'Concise and to the point' : prefs.verbosity === 'detailed' ? 'Thorough with step-by-step detail' : 'Balanced in length and depth'}\n• Tailored for the ${prefs.domain} domain\n• Optimised for ${prefs.target_model}${prefs.custom_instructions ? `\n\nAdditional context: ${prefs.custom_instructions}` : ''}`;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-900/60 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Wand2 size={14} className="text-indigo-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Live Preview
        </span>
      </div>
      <p className="text-sm text-slate-300 whitespace-pre-line leading-relaxed">
        {previewText}
      </p>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [saved, setSaved] = useState<Preferences>(DEFAULT_PREFS);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const isDirty = JSON.stringify(prefs) !== JSON.stringify(saved);

  // ── Load current preferences ─────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get('/users/me/preferences');
        const data = res.data;
        const loaded: Preferences = {
          tone: data.tone || DEFAULT_PREFS.tone,
          verbosity: data.verbosity || DEFAULT_PREFS.verbosity,
          target_model: data.target_model || DEFAULT_PREFS.target_model,
          domain: data.domain || DEFAULT_PREFS.domain,
          custom_instructions: data.custom_instructions || '',
        };
        setPrefs(loaded);
        setSaved(loaded);
      } catch {
        // Backend offline or unauthenticated — use defaults silently
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  // ── Save preferences ─────────────────────────────────────────────────────
  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus('idle');
    setErrorMsg('');
    try {
      await api.put('/users/me/preferences', {
        tone: prefs.tone,
        verbosity: prefs.verbosity,
        target_model: prefs.target_model,
        domain: prefs.domain,
        custom_instructions: prefs.custom_instructions || null,
      });
      setSaved({ ...prefs });
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setErrorMsg(Array.isArray(detail) ? detail.join(', ') : String(detail || 'Save failed'));
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const set = <K extends keyof Preferences>(key: K, val: Preferences[K]) =>
    setPrefs(p => ({ ...p, [key]: val }));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={28} className="animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Preferences</h1>
        <p className="text-slate-400 text-sm">
          Personalise how your prompts are optimised. Changes apply immediately after saving.
        </p>
      </div>

      <div className="space-y-8">

        {/* ── Tone ── */}
        <section>
          <SectionLabel>Tone</SectionLabel>
          <div className="grid grid-cols-2 gap-2">
            {TONE_OPTIONS.map(o => (
              <OptionCard
                key={o.value}
                value={o.value}
                label={o.label}
                desc={o.desc}
                selected={prefs.tone === o.value}
                onClick={() => set('tone', o.value)}
              />
            ))}
          </div>
        </section>

        {/* ── Verbosity ── */}
        <section>
          <SectionLabel>Verbosity</SectionLabel>
          <div className="grid grid-cols-3 gap-2">
            {VERBOSITY_OPTIONS.map(o => (
              <OptionCard
                key={o.value}
                value={o.value}
                label={o.label}
                desc={o.desc}
                selected={prefs.verbosity === o.value}
                onClick={() => set('verbosity', o.value)}
              />
            ))}
          </div>
        </section>

        {/* ── Domain ── */}
        <section>
          <SectionLabel>Primary Domain</SectionLabel>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {DOMAIN_OPTIONS.map(o => (
              <button
                key={o.value}
                onClick={() => set('domain', o.value)}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all duration-150 ${
                  prefs.domain === o.value
                    ? 'bg-indigo-600/15 border-indigo-500/60 shadow-md shadow-indigo-500/10'
                    : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600 hover:bg-slate-800'
                }`}
              >
                <span className="text-xl">{o.icon}</span>
                <span className={`text-xs font-medium ${prefs.domain === o.value ? 'text-indigo-300' : 'text-slate-300'}`}>
                  {o.label}
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* ── Target Model ── */}
        <section>
          <SectionLabel>Target AI Model</SectionLabel>
          <div className="grid grid-cols-2 gap-2">
            {MODEL_OPTIONS.map(o => (
              <OptionCard
                key={o.value}
                value={o.value}
                label={o.label}
                desc={o.desc}
                selected={prefs.target_model === o.value}
                onClick={() => set('target_model', o.value)}
              />
            ))}
          </div>
        </section>

        {/* ── Custom Instructions ── */}
        <section>
          <SectionLabel>Custom Instructions (optional)</SectionLabel>
          <textarea
            value={prefs.custom_instructions}
            onChange={(e) => set('custom_instructions', e.target.value)}
            placeholder="e.g. Always use simple language. Avoid technical jargon. Format output as numbered steps."
            rows={3}
            className="w-full px-4 py-3 bg-slate-800/60 border border-slate-700/60
                       rounded-xl text-sm text-slate-200 placeholder-slate-500
                       focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/20
                       resize-none transition-colors"
          />
          <p className="text-xs text-slate-500 mt-1.5">
            These instructions are injected into every prompt optimisation request.
          </p>
        </section>

        {/* ── Live Preview ── */}
        <section>
          <SectionLabel>Preview</SectionLabel>
          <PreviewPane prefs={prefs} />
        </section>

        {/* ── Save button + status ── */}
        <div className="flex items-center gap-4 pt-2">
          <button
            onClick={handleSave}
            disabled={isSaving || !isDirty}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold
                        shadow-lg transition-all duration-200 ${
              isDirty && !isSaving
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25 hover:scale-[1.02]'
                : 'bg-slate-700/60 text-slate-400 cursor-not-allowed'
            }`}
          >
            {isSaving ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                Saving...
              </>
            ) : (
              <>
                {saveStatus === 'success' ? <Check size={15} className="text-emerald-400" /> : null}
                Save preferences
              </>
            )}
          </button>

          {!isDirty && (
            <span className="text-xs text-slate-500">No unsaved changes</span>
          )}
        </div>

        {/* Success / error feedback */}
        <AnimatePresence>
          {saveStatus === 'success' && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm"
            >
              <Check size={16} />
              Preferences saved successfully!
            </motion.div>
          )}
          {saveStatus === 'error' && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
            >
              <AlertCircle size={16} />
              {errorMsg || 'Failed to save preferences. Please try again.'}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}
