import React from 'react';
import { Button } from '@/components/ui/Button/Button';
import { Card } from '@/components/ui/Card/Card';
import { Input } from '@/components/ui/Input/Input';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 lg:p-24 relative overflow-hidden">
      
      {/* Subtle Background Glow */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent/10 blur-[120px] pointer-events-none" />

      <div className="z-10 max-w-5xl w-full flex flex-col items-center text-center gap-8 animate-fadeIn">
        
        {/* Hero Section */}
        <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
          Your AI Prompts,<br />Perfected.
        </h1>
        
        <p className="text-xl text-text-secondary max-w-2xl leading-relaxed">
          Transform rough ideas into expertly crafted instructions. 
          Prompt Polisher uses an advanced RLHF-tuned language model to optimize your prompts for maximum AI performance.
        </p>

        <div className="flex gap-4 mt-4">
          <Button size="lg" variant="primary">
            Start Polishing
          </Button>
          <Button size="lg" variant="ghost">
            View Documentation
          </Button>
        </div>

        {/* Demo Component Showcase */}
        <div className="w-full mt-16 grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
          
          <Card hoverable className="animate-slideUp" style={{ animationDelay: '0.1s' }}>
            <h3 className="text-xl font-semibold mb-2">Refine Your Prompt</h3>
            <p className="text-sm text-text-muted mb-4">
              Enter your basic instructions and let our AI expand it with best practices.
            </p>
            <Input 
              multiline 
              placeholder="e.g., Write a blog post about artificial intelligence..."
              className="mb-4"
            />
            <div className="flex justify-end">
              <Button size="sm">Optimize</Button>
            </div>
          </Card>

          <Card hoverable className="animate-slideUp" style={{ animationDelay: '0.2s' }}>
            <h3 className="text-xl font-semibold mb-2">Optimized Output</h3>
            <p className="text-sm text-text-muted mb-4">
              Your prompt, enhanced with context, structure, and constraints.
            </p>
            <div className="p-4 rounded-md bg-bg-surface-elevated/50 border border-border text-sm font-mono text-text-secondary min-h-[120px] flex items-center justify-center">
              <span className="opacity-50">Awaiting input...</span>
            </div>
            <div className="flex justify-between items-center mt-4">
              <span className="text-xs text-success">Ready to copy</span>
              <Button size="sm" variant="ghost">Copy to Clipboard</Button>
            </div>
          </Card>

        </div>
      </div>
    </main>
  );
}
