import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PR Surgeon — Decompose monster Pull Requests",
  description:
    "Repository-aware AI that decomposes 300+ file Pull Requests into 5-7 small, reviewable sub-PRs in 30 seconds. Powered by IBM Bob.",
  keywords: [
    "pull request",
    "code review",
    "IBM Bob",
    "developer tools",
    "AI",
    "enterprise",
    "monorepo",
    "modernization",
  ],
  authors: [{ name: "Team Dievalivann" }],
  openGraph: {
    title: "PR Surgeon — Decompose monster Pull Requests",
    description:
      "From 400-file PR to 5 reviewable sub-PRs in 30 seconds. Powered by IBM Bob.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('pr-surgeon-theme');
                  if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="antialiased bg-white dark:bg-[#161616] text-gray-900 dark:text-gray-100 transition-colors">
        {children}
      </body>
    </html>
  );
}
