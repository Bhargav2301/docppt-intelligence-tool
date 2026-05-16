import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "DocPPT Intelligence Tool",
  description: "Professional document intelligence and PPT humanizer.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col antialiased">
        {/* Top Navigation */}
        <header className="sticky top-0 z-50 w-full border-b border-[var(--border-subtle)] bg-[var(--bg-base)]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-8">
                <Link href="/" className="font-bold text-[var(--text-primary)] text-xl tracking-tight">
                  DocPPT
                </Link>
                <nav className="hidden md:flex gap-6">
                  <Link href="/dashboard" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm font-medium transition-colors">
                    Dashboard
                  </Link>
                  <Link href="/process/doc" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm font-medium transition-colors">
                    Analyze Doc
                  </Link>
                  <Link href="/process/ppt" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm font-medium transition-colors">
                    Humanize PPT
                  </Link>
                </nav>
              </div>
              <div className="flex items-center gap-4">
                <Link href="/settings" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-sm font-medium transition-colors">
                  Settings
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 w-full mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
