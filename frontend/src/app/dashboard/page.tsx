'use client';

export default function DashboardPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center">
      <div className="max-w-md p-8 bg-slate-800/50 border border-slate-700 rounded-2xl backdrop-blur-xl">
        <h1 className="text-2xl font-bold text-white mb-2">Welcome to Prompt Polisher</h1>
        <p className="text-slate-400 mb-6">
          Your AI prompt optimization workspace. Start a new chat to polish your prompts.
        </p>
        <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors">
          New Chat
        </button>
      </div>
    </div>
  );
}
