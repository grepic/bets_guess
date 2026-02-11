import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { NavBar } from '@/components/NavBar';

export const metadata: Metadata = {
  title: 'SmartBets Pro',
  description: 'Sports analytics platform - probability estimates, fair odds, and value identification',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <Providers>
          <NavBar />
          <main className="flex-1 container-wide px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
            {children}
          </main>
          <footer className="border-t border-gray-200 bg-white mt-auto">
            <div className="container-wide px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
              <div className="text-xs text-gray-500 space-y-2 max-w-3xl">
                <p className="font-semibold text-gray-700">
                  Responsible Gambling Disclaimer
                </p>
                <p>
                  SmartBets Pro provides statistical analysis and probability estimates only.
                  These are NOT guarantees of outcomes. All sports betting involves risk and
                  you may lose money. Never bet more than you can afford to lose.
                </p>
                <p>
                  Probabilities shown are model estimates with uncertainty ranges. Past model
                  performance does not guarantee future results. Gambling should be entertaining,
                  not a source of income.
                </p>
                <p>
                  If you or someone you know has a gambling problem, call{' '}
                  <strong>1-800-522-4700</strong> (National Problem Gambling Helpline).
                </p>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
