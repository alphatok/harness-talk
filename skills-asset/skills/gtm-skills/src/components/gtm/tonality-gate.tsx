'use client';

import { useState, useEffect } from 'react';
import { Lock, ArrowRight, Check, Building2, Mail, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { isUnlocked, setUnlockState } from '@/lib/gtm-unlock';

interface TonalityGateProps {
  children: React.ReactNode;
  tonalityName: string;
}

export function TonalityGate({ children, tonalityName }: TonalityGateProps) {
  const [unlocked, setUnlocked] = useState(false);
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    setUnlocked(isUnlocked('tonalities-premium'));
  }, []);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          company,
          leadMagnet: 'tonalities-premium',
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      // Save to localStorage
      setUnlockState(email, company, 'tonalities-premium');
      setSuccess(true);

      // Show content after brief delay
      setTimeout(() => {
        setUnlocked(true);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  // During SSR or initial load, show content (will be gated on client)
  if (!isClient) {
    return <>{children}</>;
  }

  if (unlocked) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      {/* Blurred content preview */}
      <div className="blur-sm pointer-events-none select-none" aria-hidden="true">
        {children}
      </div>

      {/* Overlay gate */}
      <div className="absolute inset-0 bg-gradient-to-b from-background/50 via-background/80 to-background flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          {success ? (
            <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">You&apos;re in!</h3>
              <p className="text-zinc-400">
                All 12 premium tonalities are now unlocked. Enjoy!
              </p>
            </div>
          ) : (
            <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="h-8 w-8 text-orange-500" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">
                  Unlock {tonalityName}
                </h3>
                <p className="text-zinc-400">
                  Get instant access to all 12 premium tonalities with your email.
                </p>
              </div>

              <form onSubmit={handleUnlock} className="space-y-4">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                  <input
                    type="email"
                    placeholder="Work email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                </div>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
                  <input
                    type="text"
                    placeholder="Company name"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                </div>

                {error && (
                  <p className="text-red-400 text-sm">{error}</p>
                )}

                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
                  disabled={loading}
                >
                  {loading ? 'Unlocking...' : 'Unlock Premium Tonalities'}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>

              <div className="mt-6 pt-6 border-t border-zinc-800">
                <p className="text-zinc-500 text-sm text-center mb-3">
                  What you&apos;ll unlock:
                </p>
                <div className="grid grid-cols-2 gap-2 text-xs text-zinc-400">
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    Warren Buffett
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    Alex Hormozi
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    Naval Ravikant
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    David Ogilvy
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    SPIN Selling
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    Gap Selling
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    Sandler
                  </div>
                  <div className="flex items-center gap-1">
                    <Check className="h-3 w-3 text-orange-500" />
                    + 5 more
                  </div>
                </div>
              </div>

              <p className="text-zinc-600 text-xs text-center mt-4">
                No spam. Unsubscribe anytime.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
