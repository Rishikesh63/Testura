# Testura — AI Testing for Vibe-Coded Apps

Connect your GitHub repo. AI writes and runs tests automatically. Zero manual work.

## Stack
- **Frontend**: Next.js 14 + Tailwind CSS
- **Backend**: Python + FastAPI
- **AI**: Claude API (Anthropic)
- **Database**: Supabase (PostgreSQL)
- **Queue**: Redis
- **Hosting**: Vercel (frontend) + Railway (backend)

## Project Structure
```
Testura/
├── frontend/          # Next.js app
├── backend/           # FastAPI API server
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Analyzer, Generator, Runner
│   │   ├── models/    # Pydantic models
│   │   └── services/  # GitHub service
│   └── main.py
├── docker/            # Docker compose + sandbox
└── github-action/     # GitHub Action integration
```

## Quick Start

### 1. Clone and configure
```bash
git clone <your-repo>

# Backend
cp backend/.env.example backend/.env
# Fill in your keys (Supabase, Anthropic, GitHub OAuth, Stripe)

# Frontend
cp frontend/.env.example frontend/.env.local
# Fill in Supabase public keys
```

### 2. Run with Docker
```bash
cd docker
docker-compose up
```

### 3. Run locally (dev)
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)
| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com |
| `GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth app secret |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `REDIS_URL` | Redis connection URL |

### Frontend (`frontend/.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## Supabase Tables

Run these in your Supabase SQL editor:

```sql
create table repos (
  id uuid primary key,
  full_name text not null,
  repo_url text not null,
  language text,
  last_run_at timestamptz,
  last_run_status text,
  tests_passed int default 0,
  tests_total int default 0,
  created_at timestamptz default now()
);

create table test_runs (
  id uuid primary key,
  repo_id uuid references repos(id) on delete cascade,
  status text not null default 'running',
  tests_passed int default 0,
  tests_failed int default 0,
  tests_total int default 0,
  duration_ms int default 0,
  results jsonb default '[]',
  created_at timestamptz default now()
);
```

## GitHub Action Usage

Add to `.github/workflows/test.yml` in any repo:

```yaml
name: AI Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: your-username/testura-action@v1
        with:
          api_url: https://your-api.railway.app
          api_key: ${{ secrets.TESTURA_API_KEY }}
          repo_id: ${{ secrets.TESTURA_REPO_ID }}
```

## Pricing
| Plan | Price | Limits |
|---|---|---|
| Free | $0/mo | 1 repo, 50 tests/month |
| Starter | $29/mo | 3 repos, 500 tests/month |
| Pro | $79/mo | 10 repos, unlimited |
| Team | $149/mo | Unlimited + CI/CD |
