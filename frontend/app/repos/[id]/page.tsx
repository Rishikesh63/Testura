"use client";
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { repoApi, testApi } from "@/lib/api";
import { formatDate, passRate } from "@/lib/utils";
import {
  ArrowLeft, Play, RefreshCw, CheckCircle,
  XCircle, AlertCircle, ChevronDown, ChevronUp, Zap,
} from "lucide-react";
import { toast } from "sonner";

type TestResult = {
  id: string;
  name: string;
  file: string;
  status: "passed" | "failed" | "error";
  duration_ms: number;
  error_message?: string;
  fix_suggestion?: string;
};

type TestRun = {
  id: string;
  status: "running" | "passed" | "failed";
  created_at: string;
  duration_ms: number;
  tests_passed: number;
  tests_failed: number;
  tests_total: number;
  results: TestResult[];
};

type Repo = {
  id: string;
  full_name: string;
};

export default function RepoDetail() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [repo, setRepo] = useState<Repo | null>(null);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<TestRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  async function fetchData() {
    try {
      const [repoRes, runsRes] = await Promise.all([
        repoApi.get(id),
        testApi.listRuns(id),
      ]);
      setRepo(repoRes.data);
      setRuns(runsRes.data.runs);
      if (runsRes.data.runs.length > 0) setSelectedRun(runsRes.data.runs[0]);
    } catch {
      toast.error("Failed to load repo data");
    } finally {
      setLoading(false);
    }
  }

  async function runTests() {
    setRunning(true);
    try {
      const { data } = await testApi.run(id);
      toast.success("Test run started");
      // Poll for results
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const { data: runData } = await testApi.getRun(id, data.run_id);
        if (runData.status !== "running" || attempts >= 40) {
          clearInterval(poll);
          fetchData();
          setRunning(false);
        }
      }, 3000);
    } catch {
      toast.error("Failed to start test run");
      setRunning(false);
    }
  }

  if (loading) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-gray-700">
            <ArrowLeft size={20} />
          </button>
          <div className="flex items-center gap-2 font-bold text-lg">
            <Zap className="text-blue-600" size={18} />
            {repo?.full_name}
          </div>
        </div>
        <button
          onClick={runTests}
          disabled={running}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-2 disabled:opacity-60"
        >
          {running ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
          {running ? "Running..." : "Run Tests"}
        </button>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 flex gap-6">
        {/* Sidebar: run history */}
        <div className="w-64 shrink-0">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Run History</h2>
          <div className="space-y-2">
            {runs.length === 0 && (
              <p className="text-sm text-gray-400">No runs yet. Click Run Tests.</p>
            )}
            {runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedRun(run)}
                className={`w-full text-left p-3 rounded-xl border text-sm transition ${
                  selectedRun?.id === run.id ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white hover:border-gray-300"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {run.status === "passed" && <CheckCircle size={14} className="text-green-500" />}
                  {run.status === "failed" && <XCircle size={14} className="text-red-500" />}
                  {run.status === "running" && <RefreshCw size={14} className="text-blue-500 animate-spin" />}
                  <span className="font-medium capitalize">{run.status}</span>
                </div>
                <div className="text-gray-400 text-xs">{formatDate(run.created_at)}</div>
                <div className="text-xs mt-1 text-gray-500">
                  {run.tests_passed}/{run.tests_total} passed
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main: test results */}
        <div className="flex-1">
          {!selectedRun ? (
            <div className="text-center py-20 text-gray-400">
              <Play size={40} className="mx-auto mb-4 opacity-30" />
              <p>Run tests to see results here.</p>
            </div>
          ) : (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                  { label: "Pass Rate", value: `${passRate(selectedRun.tests_passed, selectedRun.tests_total)}%`, color: "text-green-600" },
                  { label: "Passed", value: selectedRun.tests_passed, color: "text-green-600" },
                  { label: "Failed", value: selectedRun.tests_failed, color: "text-red-500" },
                  { label: "Duration", value: `${(selectedRun.duration_ms / 1000).toFixed(1)}s`, color: "text-gray-700" },
                ].map((s) => (
                  <div key={s.label} className="bg-white border rounded-xl p-4 text-center">
                    <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                    <div className="text-xs text-gray-400 mt-1">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Test results list */}
              {selectedRun.results.length === 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-sm text-yellow-800">
                  <p className="font-semibold mb-1">No test results found</p>
                  <p className="text-yellow-700">
                    Tests were generated but could not be run. This usually means Jest is not installed in the repo.
                    Install Jest globally: <code className="bg-yellow-100 px-1 rounded">npm install -g jest</code> then run again.
                  </p>
                </div>
              )}
              <div className="space-y-2">
                {selectedRun.results.map((test) => (
                  <div key={test.id} className="bg-white border rounded-xl overflow-hidden">
                    <button
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
                      onClick={() => setExpandedTest(expandedTest === test.id ? null : test.id)}
                    >
                      <div className="flex items-center gap-3">
                        {test.status === "passed" && <CheckCircle size={16} className="text-green-500 shrink-0" />}
                        {test.status === "failed" && <XCircle size={16} className="text-red-500 shrink-0" />}
                        {test.status === "error" && <AlertCircle size={16} className="text-yellow-500 shrink-0" />}
                        <div>
                          <div className="font-medium text-sm text-gray-800">{test.name}</div>
                          <div className="text-xs text-gray-400">{test.file}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span>{test.duration_ms}ms</span>
                        {expandedTest === test.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </div>
                    </button>

                    {expandedTest === test.id && (test.error_message || test.fix_suggestion) && (
                      <div className="border-t px-4 py-4 space-y-3">
                        {test.error_message && (
                          <div>
                            <div className="text-xs font-semibold text-red-500 mb-1">Error</div>
                            <pre className="bg-red-50 text-red-700 text-xs p-3 rounded-lg overflow-auto">
                              {test.error_message}
                            </pre>
                          </div>
                        )}
                        {test.fix_suggestion && (
                          <div>
                            <div className="text-xs font-semibold text-blue-600 mb-1 flex items-center gap-1">
                              <Zap size={12} /> AI Fix Suggestion
                            </div>
                            <div className="bg-blue-50 text-blue-800 text-xs p-3 rounded-lg leading-relaxed">
                              {test.fix_suggestion}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
