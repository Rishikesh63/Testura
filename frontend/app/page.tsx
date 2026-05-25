"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signInWithGitHub, getSupabase } from "@/lib/supabase";
import { Github, Zap, ShieldCheck, BarChart3, ArrowRight, CheckCircle } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();
  const [stats, setStats] = useState({ repos: 0, tests_run: 0, highest_pass_rate: 0 });

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/stats`)
      .then((r) => r.json())
      .then((d) => setStats(d))
      .catch(() => {});
  }, []);

  async function handlePricingCta(planId: string) {
    const { data } = await getSupabase().auth.getSession();
    if (data.session) {
      router.push(planId === "free" ? "/dashboard" : "/billing");
    } else {
      signInWithGitHub();
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center gap-2 font-bold text-xl">
          <Zap className="text-blue-600" size={22} />
          Testura
        </div>
        <div className="flex items-center gap-6 text-sm text-gray-600">
          <a href="#how-it-works" className="hover:text-gray-900">How it works</a>
          <a href="#pricing" className="hover:text-gray-900">Pricing</a>
          <button
            onClick={signInWithGitHub}
            className="bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <Github size={16} /> Sign in with GitHub
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full mb-6">
          <ShieldCheck size={14} /> 58% of vibe-coded apps ship without tests
        </div>
        <h1 className="text-5xl font-bold text-gray-900 leading-tight mb-6">
          AI writes and runs tests<br />for your code. Automatically.
        </h1>
        <p className="text-xl text-gray-500 mb-10 max-w-2xl mx-auto">
          Connect your GitHub repo. Testura reads your code, generates tests,
          runs them, and tells you what broke — zero manual work required.
        </p>
        <button
          onClick={signInWithGitHub}
          className="bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-medium hover:bg-blue-700 flex items-center gap-3 mx-auto"
        >
          <Github size={20} />
          Connect GitHub — it's free
          <ArrowRight size={20} />
        </button>
        <p className="text-sm text-gray-400 mt-4">No credit card. Free tier includes 1 repo + 50 tests/month.</p>
      </section>

      {/* Live stats */}
      <section className="bg-gray-50 py-14 border-y">
        <div className="max-w-4xl mx-auto px-6">
          <p className="text-center text-sm text-gray-400 uppercase tracking-widest mb-8">Live platform stats</p>
          <div className="grid grid-cols-3 gap-6 text-center">
            {[
              { value: stats.repos > 0 ? stats.repos.toLocaleString() : "—", label: "Repos analyzed" },
              { value: stats.tests_run > 0 ? stats.tests_run.toLocaleString() : "—", label: "Tests run" },
              { value: stats.highest_pass_rate > 0 ? `${stats.highest_pass_rate}%` : "—", label: "Highest pass rate" },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-2xl border p-6">
                <div className="text-4xl font-bold text-blue-600 mb-1">{s.value}</div>
                <div className="text-sm text-gray-500">{s.label}</div>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-gray-400 mt-6">Built for developers using Cursor · Lovable · Bolt · v0 · Replit</p>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="max-w-5xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center mb-16">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {[
            {
              icon: <Github size={28} className="text-blue-600" />,
              step: "1",
              title: "Connect your repo",
              desc: "Sign in with GitHub and select any repository. Testura clones it and reads your entire codebase.",
            },
            {
              icon: <Zap size={28} className="text-blue-600" />,
              step: "2",
              title: "AI generates tests",
              desc: "Our AI analyzes every function, route, and component — then writes comprehensive unit and integration tests.",
            },
            {
              icon: <BarChart3 size={28} className="text-blue-600" />,
              step: "3",
              title: "See results instantly",
              desc: "Tests run in a secure sandbox. View pass/fail results, coverage %, and AI-powered fix suggestions.",
            },
          ].map((item) => (
            <div key={item.step} className="text-center">
              <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                {item.icon}
              </div>
              <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-16">Everything you need</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              "Unit + integration tests generated automatically",
              "Works with JavaScript, TypeScript, and Python",
              "GitHub Actions integration — runs on every PR",
              "AI explains why tests fail and how to fix them",
              "Diff-aware — only re-tests changed files",
              "Slack + email alerts when tests break",
              "Coverage report per file and function",
              "No config files needed — zero setup",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 bg-white p-4 rounded-xl border">
                <CheckCircle size={18} className="text-green-500 shrink-0" />
                <span className="text-gray-700 text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-5xl mx-auto px-6 py-24">
        <h2 className="text-3xl font-bold text-center mb-4">Simple pricing</h2>
        <p className="text-center text-gray-500 mb-16">Start free. Upgrade when you need more.</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { id: "free",    name: "Free",    price: "₹0",      features: ["1 repo", "50 tests/mo", "Dashboard access"], cta: "Get started",       highlight: false },
            { id: "starter", name: "Starter", price: "₹999",    features: ["3 repos", "500 tests/mo", "Email alerts"],    cta: "Upgrade to Starter", highlight: false },
            { id: "pro",     name: "Pro",     price: "₹2,499",  features: ["10 repos", "Unlimited tests", "Priority support"], cta: "Upgrade to Pro", highlight: true },
            { id: "team",    name: "Team",    price: "₹4,999",  features: ["Unlimited repos", "CI/CD integration", "Team dashboard"], cta: "Contact us", highlight: false },
          ].map((plan) => (
            <div
              key={plan.name}
              className={`p-6 rounded-2xl border-2 flex flex-col ${plan.highlight ? "border-blue-600 bg-blue-50" : "border-gray-200"}`}
            >
              <div className="font-bold text-lg mb-1">{plan.name}</div>
              <div className="text-3xl font-bold mb-1">{plan.price}<span className="text-sm font-normal text-gray-500">/mo</span></div>
              <ul className="mt-4 space-y-2 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="text-sm text-gray-600 flex items-center gap-2">
                    <CheckCircle size={14} className="text-green-500" /> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handlePricingCta(plan.id)}
                className={`mt-6 py-2 rounded-lg text-sm font-medium ${plan.highlight ? "bg-blue-600 text-white hover:bg-blue-700" : "bg-gray-900 text-white hover:bg-gray-700"}`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-10 text-center text-sm text-gray-400">
        <div className="flex items-center justify-center gap-2 font-semibold text-gray-600 mb-2">
          <Zap size={16} className="text-blue-600" /> Testura
        </div>
        <p>AI-powered testing for the vibe coding era.</p>
      </footer>
    </div>
  );
}
