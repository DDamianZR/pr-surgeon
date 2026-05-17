"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Scissors, Loader2, AlertCircle, ArrowRight } from "lucide-react";

const EXAMPLE_PRS = [
  {
    label: "Django: CompositePrimaryKey",
    url: "https://github.com/django/django/pull/18056",
    files: 43,
    hot: true,
  },
  {
    label: "Desbordante: AR validation",
    url: "https://github.com/Tydik42/desbordante-core/pull/2",
    files: 61,
    hot: false,
  },
  {
    label: "Feedback-v2: Next.js 14 → 15",
    url: "https://github.com/diegomez/feedback-v2/pull/9",
    files: 64,
    hot: false,
  },
];

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStage, setLoadingStage] = useState("");

  async function analyze(prUrl: string) {
    setLoading(true);
    setError(null);
    setUrl(prUrl);

    const stages = [
      "Fetching PR from GitHub...",
      "Parsing changed files...",
      "Building dependency graph...",
      "Detecting clusters with community detection...",
      "Decomposing into sub-PRs...",
      "Enriching with descriptions...",
    ];

    let stageIdx = 0;
    setLoadingStage(stages[0]);
    const stageInterval = setInterval(() => {
      stageIdx = Math.min(stageIdx + 1, stages.length - 1);
      setLoadingStage(stages[stageIdx]);
    }, 500);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pr_url: prUrl, max_files: 200 }),
      });

      clearInterval(stageInterval);

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(detail.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      sessionStorage.setItem("pr-surgeon-analysis", JSON.stringify(data));
      router.push("/analysis");
    } catch (e) {
      clearInterval(stageInterval);
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (url.trim()) analyze(url.trim());
  }

  return (
    <main className="min-h-screen bg-white relative overflow-hidden">
      {/* Background grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#0f62fe 1px, transparent 1px), linear-gradient(90deg, #0f62fe 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Header */}
      <header className="relative border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Scissors className="w-5 h-5 text-ibm-blue" strokeWidth={2.5} />
            <span className="font-semibold tracking-tight text-gray-900">
              PR Surgeon
            </span>
          </div>
          <div className="text-xs text-gray-500 hidden md:block">
            Built with{" "}
            <span className="font-medium text-gray-900">IBM Bob</span> for the Bob Hackathon 2026
          </div>
        </div>
      </header>

      <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-12">
        {/* Hero */}
        <div className="mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-100 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-ibm-blue animate-pulse" />
            <span className="text-xs font-medium text-ibm-blue-dark">
              Repository-aware AI · Powered by IBM Bob
            </span>
          </div>

          <h1 className="text-5xl md:text-6xl font-semibold tracking-tight text-gray-900 leading-[1.05] mb-6">
            Decompose monster
            <br />
            <span className="text-ibm-blue">Pull Requests</span> safely.
          </h1>

          <p className="text-lg text-gray-600 max-w-2xl leading-relaxed">
            Enterprise migrations produce 300+ file PRs that sit open for{" "}
            <span className="font-medium text-gray-900">4–8 weeks</span> and cost{" "}
            <span className="font-medium text-gray-900">$15K–25K</span> in
            engineer review time. PR Surgeon turns one monster PR into 5–7
            reviewable sub-PRs in <span className="font-medium text-gray-900">30 seconds</span>.
          </p>
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="mb-6">
          <div className="flex flex-col md:flex-row gap-2 p-1 bg-white border-2 border-gray-200 rounded-lg focus-within:border-ibm-blue transition-colors shadow-sm">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo/pull/123"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-transparent text-gray-900 placeholder-gray-400 focus:outline-none disabled:opacity-50 font-mono text-sm"
            />
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="px-6 py-3 bg-ibm-blue text-white font-medium rounded-md hover:bg-ibm-blue-dark transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 min-w-[140px]"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing</span>
                </>
              ) : (
                <>
                  <span>Analyze PR</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Loading stage display */}
        {loading && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-lg">
            <div className="flex items-center gap-3 text-sm text-ibm-blue-dark">
              <Loader2 className="w-4 h-4 animate-spin shrink-0" />
              <span className="font-mono">{loadingStage}</span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-ibm-red shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-900 mb-1">
                Analysis failed
              </div>
              <div className="text-sm text-red-700 font-mono">{error}</div>
            </div>
          </div>
        )}

        {/* Example PRs */}
        <div className="mt-12">
          <div className="text-xs font-medium uppercase tracking-wider text-gray-500 mb-3">
            Or try a real-world example
          </div>
          <div className="grid gap-2">
            {EXAMPLE_PRS.map((pr) => (
              <button
                key={pr.url}
                onClick={() => !loading && analyze(pr.url)}
                disabled={loading}
                className="group text-left p-4 border border-gray-200 rounded-lg hover:border-ibm-blue hover:bg-blue-50/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="font-medium text-gray-900 truncate">
                      {pr.label}
                    </div>
                    {pr.hot && (
                      <span className="shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-ibm-blue text-white rounded">
                        Demo
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0 text-sm text-gray-500">
                    <span className="font-mono">{pr.files} files</span>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-ibm-blue group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <footer className="relative border-t border-gray-200 mt-20">
        <div className="max-w-6xl mx-auto px-6 py-6 text-xs text-gray-500">
          PR Surgeon · IBM Bob Hackathon 2026 · Team Dievalivann
        </div>
      </footer>
    </main>
  );
}
