import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VASP-Trace | Cryptocurrency Wallet Attribution Platform",
  description:
    "Automated attribution of unknown cryptocurrency wallets to nearest VASPs for investigative leads.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

  return (
    <html lang="en">
      <body className="antialiased flex flex-col min-h-screen">
        {/* Persistent SYNTHETIC DATA ribbon per PRD 7.7 */}
        {isDemoMode && (
          <div className="bg-amber-500 text-slate-950 font-semibold px-4 py-1.5 text-center text-xs tracking-wider uppercase border-b border-amber-600 shadow-sm flex items-center justify-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-slate-950 animate-pulse"></span>
            SYNTHETIC DATA — FOR DEMONSTRATION PURPOSES ONLY · NO REAL ADDRESSES
          </div>
        )}

        <header className="bg-slate-900 border-b border-slate-800 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 text-white px-2.5 py-1 rounded font-black tracking-tight text-lg shadow-sm">
              VT
            </div>
            <div>
              <h1 className="font-bold text-base tracking-wide leading-none">
                VASP-Trace
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Cryptocurrency Wallet Attribution & Lawful Disclosure Intelligence
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-xs text-slate-400">
            <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              SIH-26182
            </span>
            <span className="px-2.5 py-1 rounded-full bg-blue-900/40 border border-blue-700/50 text-blue-300">
              MVP v0.1
            </span>
          </div>
        </header>

        <main className="flex-1 flex flex-col">{children}</main>

        <footer className="border-t border-slate-200 bg-white py-3 px-6 text-center text-xs text-slate-500">
          VASP-Trace · SIH26182 · Attribution leads are investigative indicators, not proof of ownership or culpability.
        </footer>
      </body>
    </html>
  );
}
