import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PR Surgeon",
  description: "Decompose monster Pull Requests into safe, reviewable sub-PRs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

// Made with Bob
