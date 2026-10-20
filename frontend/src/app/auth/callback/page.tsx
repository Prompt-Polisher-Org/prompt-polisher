'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [error, setError] = useState('');
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const url = new URL(window.location.href);
    const tokens = new URLSearchParams(url.hash.slice(1));
    const accessToken = tokens.get('access_token');
    const refreshToken = tokens.get('refresh_token');

    // Remove credentials and provider error details from the visible URL as
    // soon as the callback page has read them.
    window.history.replaceState({}, document.title, url.pathname);

    if (!accessToken || !refreshToken) {
      setError('Sign-in did not complete. Please try again.');
      return;
    }

    login({ access_token: accessToken, refresh_token: refreshToken });
    router.replace('/dashboard');
  }, [login, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-900 px-6 text-center text-slate-200">
      {error ? (
        <>
          <p role="alert">{error}</p>
          <Link className="text-indigo-400 underline" href="/login">Return to sign in</Link>
        </>
      ) : (
        <>
          <Loader2 className="animate-spin text-indigo-400" aria-hidden="true" />
          <p>Completing sign-in…</p>
        </>
      )}
    </main>
  );
}
