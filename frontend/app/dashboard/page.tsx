"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { repoApi, testApi } from "@/lib/api";
import { supabase, signOut } from "@/lib/supabase";
import { formatDate, passRate } from "@/lib/utils";
import {
  Github, Plus, Zap, LogOut, Play, Trash2,
  CheckCircle, XCircle, Clock, RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

type Repo = {
  id: string;
  name: string;
  full_name: string;
  last_run_at: string | null;
  last_run_status: "passed" | "failed" | "running" | null;
  tests_passed: number;
  tests_total: number;
};

export default function Dashboard() {
  const router = useRouter();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [repoUrl, setRepoUrl] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [runningRepoId, setRunningRepoId] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) router.push("/");
    });
    fetchRepos();
  }, []);

  async function fetchRepos() {
    try {
      const { data } = await repoApi.list();
      setRepos(data.repos);
    } catch {
      toast.error("Failed to load repos");
    } finally {
      setLoading(false);
    }
  }

  async function connectRepo() {
    if (!repoUrl.trim()) return;
    setConnecting(true);
    try {
      await repoApi.connect(repoUrl.trim());
      toast.success("Repo connected successfully");
      setRepoUrl("");
      fetchRepos();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Failed to connect repo");
    } finally {
      setConnecting(false);
    }
  }

  async function runTests(repoId: string) {
    setRunningRepoId(repoId);
    try {
      await testApi.run(repoId);
      toast.success("Test run started");
      setTimeout(fetchRepos, 2000);
    } catch {
      toast.error("Failed to start test run");
    } finally {
      setRunningRepoId(null);
    }
  }

  async function deleteRepo(repoId: string) {
    try {
      await repoApi.delete(repoId);
      toast.success("Repo removed");
      setRepos((r) => r.filter((x) => x.id !== repoId));
    } catch {
      toast.error("Failed to remove repo");
    }
  }

  const statusIcon = (status: Repo["last_run_status"]) => {
    if (status === "passed") return <CheckCircle size={16} className="text-green-500" />;
    if (status === "failed") return <XCircle size={16} className="text-red-500" />;
    if (status === "running") return <RefreshCw size={16} className="text-blue-500 animate-spin" />;
    return <Clock size={16} className="text-gray-400" />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-xl">
          <Zap className="text-blue-600" size={20} />
          TestPilot
        </div>
        <button
          onClick={() => signOut().then(() => router.push("/"))}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800"
        >
          <LogOut size={16} /> Sign out
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Your Repositories</h1>
        </div>

        {/* Connect repo */}
        <div className="bg-white border rounded-xl p-5 mb-8 flex gap-3">
          <input
            type="text"
            placeholder="https://github.com/username/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && connectRepo()}
            className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={connectRepo}
            disabled={connecting}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-2 disabled:opacity-60"
          >
            {connecting ? <RefreshCw size={16} className="animate-spin" /> : <Plus size={16} />}
            Connect Repo
          </button>
        </div>

        {/* Repo list */}
        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading...</div>
        ) : repos.length === 0 ? (
          <div className="text-center py-20">
            <Github size={40} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No repos connected yet.</p>
            <p className="text-gray-400 text-sm">Paste a GitHub URL above to get started.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {repos.map((repo) => (
              <div key={repo.id} className="bg-white border rounded-xl p-5 flex items-center justify-between hover:border-blue-200 transition">
                <div
                  className="flex items-center gap-4 cursor-pointer flex-1"
                  onClick={() => router.push(`/repos/${repo.id}`)}
                >
                  <Github size={20} className="text-gray-400 shrink-0" />
                  <div>
                    <div className="font-medium text-gray-900">{repo.full_name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {repo.last_run_at ? `Last run ${formatDate(repo.last_run_at)}` : "Never run"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  {repo.tests_total > 0 && (
                    <div className="text-center">
                      <div className="text-lg font-bold text-gray-800">
                        {passRate(repo.tests_passed, repo.tests_total)}%
                      </div>
                      <div className="text-xs text-gray-400">pass rate</div>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-sm">
                    {statusIcon(repo.last_run_status)}
                    <span className="text-gray-500 capitalize">
                      {repo.last_run_status || "Not run"}
                    </span>
                  </div>

                  <button
                    onClick={() => runTests(repo.id)}
                    disabled={runningRepoId === repo.id}
                    className="flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-100 disabled:opacity-60"
                  >
                    {runningRepoId === repo.id
                      ? <RefreshCw size={14} className="animate-spin" />
                      : <Play size={14} />}
                    Run Tests
                  </button>

                  <button
                    onClick={() => deleteRepo(repo.id)}
                    className="text-gray-300 hover:text-red-500 p-1"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
