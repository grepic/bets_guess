import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'SmartBets Pro',
  description: 'Sports analytics platform - probability estimates, fair odds, and value identification',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-14">
                <a href="/" className="flex items-center gap-2">
                  <span className="text-xl font-bold text-brand-700">SmartBets</span>
                  <span className="text-xs bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full font-medium">
                    PRO
                  </span>
                </a>
                <nav className="flex items-center gap-6 text-sm font-medium text-gray-600">
                  <a href="/" className="hover:text-brand-600 transition-colors">Dashboard</a>
                  <a href="/odds-moves" className="hover:text-brand-600 transition-colors">Odds Moves</a>
                  <a href="/alerts" className="hover:text-brand-600 transition-colors">Alerts</a>
                  <a href="/models" className="hover:text-brand-600 transition-colors">Models</a>
                </nav>
              </div>
            </div>
          </header>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
          <footer className="border-t border-gray-200 bg-white mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <div className="text-xs text-gray-500 space-y-2">
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
