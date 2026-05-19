-- Run this entire file in Supabase SQL Editor
-- Dashboard → SQL Editor → New query → paste → Run

-- ============================================================
-- REPOS TABLE
-- ============================================================
create table if not exists public.repos (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade,
  full_name   text not null,
  repo_url    text not null,
  language    text,
  last_run_at timestamptz,
  last_run_status text check (last_run_status in ('passed', 'failed', 'running')),
  tests_passed int not null default 0,
  tests_total  int not null default 0,
  created_at  timestamptz not null default now()
);

-- Each user can only connect a repo once
create unique index if not exists repos_user_repo_url
  on public.repos(user_id, repo_url);

-- ============================================================
-- TEST RUNS TABLE
-- ============================================================
create table if not exists public.test_runs (
  id           uuid primary key default gen_random_uuid(),
  repo_id      uuid not null references public.repos(id) on delete cascade,
  status       text not null default 'running'
                 check (status in ('running', 'passed', 'failed')),
  tests_passed int not null default 0,
  tests_failed int not null default 0,
  tests_total  int not null default 0,
  duration_ms  int not null default 0,
  results      jsonb not null default '[]'::jsonb,
  created_at   timestamptz not null default now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table public.repos     enable row level security;
alter table public.test_runs enable row level security;

-- Users can only see their own repos
create policy "users_own_repos" on public.repos
  for all using (auth.uid() = user_id);

-- Users can only see runs for their own repos
create policy "users_own_runs" on public.test_runs
  for all using (
    repo_id in (
      select id from public.repos where user_id = auth.uid()
    )
  );

-- ============================================================
-- INDEXES (for fast queries)
-- ============================================================
create index if not exists idx_repos_user_id
  on public.repos(user_id);

create index if not exists idx_test_runs_repo_id
  on public.test_runs(repo_id);

create index if not exists idx_test_runs_created_at
  on public.test_runs(created_at desc);
