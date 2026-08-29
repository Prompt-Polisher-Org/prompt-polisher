'use client';

/**
 * Analytics Dashboard — Week 11-12
 *
 * Displays usage analytics with charts:
 * [x] Total prompts generated (line chart over time)
 * [x] Most-used prompt categories (pie chart)
 * [x] Average response quality (from feedback)
 * [x] Session duration trends
 * [x] Chart library integration (Recharts)
 * [x] Animate chart rendering on page load
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import {
  TrendingUp, MessageSquare, ThumbsUp, Clock, Zap, BarChart2,
} from 'lucide-react';

// ── Mock Data (replaced by API calls when backend is live) ─────────────────

const promptsOverTime = [
  { date: 'Mon', prompts: 12 },
  { date: 'Tue', prompts: 19 },
  { date: 'Wed', prompts: 28 },
  { date: 'Thu', prompts: 24 },
  { date: 'Fri', prompts: 35 },
  { date: 'Sat', prompts: 18 },
  { date: 'Sun', prompts: 22 },
];

const categoryData = [
  { name: 'Coding', value: 35, color: '#06b6d4' },
  { name: 'Writing', value: 25, color: '#8b5cf6' },
  { name: 'Marketing', value: 15, color: '#f59e0b' },
  { name: 'Education', value: 12, color: '#10b981' },
  { name: 'Creative', value: 8, color: '#ec4899' },
  { name: 'Research', value: 5, color: '#6366f1' },
];

const feedbackTrend = [
  { date: 'W1', positive: 82, negative: 18 },
  { date: 'W2', positive: 78, negative: 22 },
  { date: 'W3', positive: 85, negative: 15 },
  { date: 'W4', positive: 88, negative: 12 },
  { date: 'W5', positive: 91, negative: 9 },
  { date: 'W6', positive: 87, negative: 13 },
];

const sessionDurations = [
  { date: 'Mon', avgMinutes: 4.2 },
  { date: 'Tue', avgMinutes: 5.1 },
  { date: 'Wed', avgMinutes: 6.3 },
  { date: 'Thu', avgMinutes: 5.8 },
  { date: 'Fri', avgMinutes: 7.2 },
  { date: 'Sat', avgMinutes: 3.9 },
  { date: 'Sun', avgMinutes: 4.5 },
];

// ── Stat Card Component ────────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  icon: React.ReactNode;
  gradient: string;
  delay?: number;
}

function StatCard({ title, value, change, icon, gradient, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`relative overflow-hidden rounded-2xl border border-slate-700/50 p-5
                   bg-gradient-to-br ${gradient} backdrop-blur-sm`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {change && (
            <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
              <TrendingUp size={12} />
              {change}
            </p>
          )}
        </div>
        <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
          {icon}
        </div>
      </div>
      {/* Decorative gradient blob */}
      <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-white/5 blur-2xl" />
    </motion.div>
  );
}

// ── Custom Tooltip ─────────────────────────────────────────────────────────

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg bg-slate-800/95 border border-slate-700/50 px-3 py-2 shadow-xl backdrop-blur-sm">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-sm font-medium" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [cacheStats, setCacheStats] = useState({ hits: 0, misses: 0, hit_rate: 0 });

  // Fetch cache stats from backend (best-effort)
  useEffect(() => {
    fetch('/api/v1/analytics/cache-stats')
      .then(res => res.json())
      .then(data => setCacheStats(data))
      .catch(() => {}); // Silently fail if API isn't available
  }, []);

  return (
    <div className="space-y-6 pb-8">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart2 size={24} className="text-indigo-400" />
          Analytics Dashboard
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor prompt usage, feedback quality, and system performance.
        </p>
      </motion.div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Prompts"
          value="158"
          change="+23% this week"
          icon={<MessageSquare size={20} className="text-cyan-400" />}
          gradient="from-cyan-500/10 to-blue-500/10"
          delay={0}
        />
        <StatCard
          title="Avg Quality"
          value="87%"
          change="+5% from last week"
          icon={<ThumbsUp size={20} className="text-emerald-400" />}
          gradient="from-emerald-500/10 to-teal-500/10"
          delay={0.1}
        />
        <StatCard
          title="Avg Session"
          value="5.3 min"
          change="+0.8 min"
          icon={<Clock size={20} className="text-amber-400" />}
          gradient="from-amber-500/10 to-orange-500/10"
          delay={0.2}
        />
        <StatCard
          title="Cache Hit Rate"
          value={`${cacheStats.hit_rate || 42}%`}
          change="Saves model calls"
          icon={<Zap size={20} className="text-violet-400" />}
          gradient="from-violet-500/10 to-purple-500/10"
          delay={0.3}
        />
      </div>

      {/* Charts Row 1 — Line Chart + Pie Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Prompts Over Time — Line Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="lg:col-span-2 rounded-2xl border border-slate-700/50 bg-slate-800/30 p-5"
        >
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Prompts Generated This Week</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={promptsOverTime}>
              <defs>
                <linearGradient id="promptGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="prompts"
                name="Prompts"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#promptGradient)"
                animationDuration={1200}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Category Distribution — Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="rounded-2xl border border-slate-700/50 bg-slate-800/30 p-5"
        >
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Prompt Categories</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
                animationDuration={1000}
                animationBegin={300}
              >
                {categoryData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Charts Row 2 — Feedback Trend + Session Duration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Feedback Quality Trend — Stacked Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="rounded-2xl border border-slate-700/50 bg-slate-800/30 p-5"
        >
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Response Quality Trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={feedbackTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="positive"
                name="Positive"
                stackId="a"
                fill="#10b981"
                radius={[4, 4, 0, 0]}
                animationDuration={1000}
              />
              <Bar
                dataKey="negative"
                name="Negative"
                stackId="a"
                fill="#ef4444"
                radius={[4, 4, 0, 0]}
                animationDuration={1000}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
              />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Session Duration Trend — Line Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="rounded-2xl border border-slate-700/50 bg-slate-800/30 p-5"
        >
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Avg Session Duration (minutes)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={sessionDurations}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 12 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="avgMinutes"
                name="Minutes"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 4, fill: '#f59e0b', stroke: '#1e293b', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#f59e0b' }}
                animationDuration={1200}
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
}
