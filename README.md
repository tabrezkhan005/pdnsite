# Perin Devi Natyalayam

Website and student portal for **Perin Devi Natyalayam**, a Kuchipudi classical dance school.

## Repository structure

```
├── frontend/        # Next.js (TypeScript, App Router, Tailwind v4)
├── backend/         # Django REST API (Python 3.12+)
├── infra/           # Infrastructure configs (Dockerfiles, nginx, etc.)
├── docs/            # Architecture decisions, runbooks, deployment notes
├── .github/         # CI/CD workflows
├── docker-compose.yml
├── package.json     # Root npm scripts (cross-platform task runner)
└── .editorconfig
```

## Prerequisites

| Tool           | Version  |
| -------------- | -------- |
| Node.js        | LTS (22) |
| Python         | 3.12+    |
| Docker Desktop | Latest   |

## Quick start

### Frontend (Next.js)

```powershell
cd frontend
npm install
npm run dev          # http://localhost:3000
```

### Backend (Django) — via Docker

```powershell
# From repo root
npm run docker:up    # Starts Postgres, Redis, backend, Celery
npm run docker:migrate
# API available at http://localhost:8000
```

### Backend (Django) — local Python

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
cp .env.example .env   # then edit .env
python manage.py migrate
python manage.py seed      # Optional: seeds realistic demo data
python manage.py runserver
```

## Root npm scripts

| Script              | Description                                  |
| ------------------- | -------------------------------------------- |
| `frontend:dev`      | Start Next.js dev server                     |
| `frontend:build`    | Production build of the frontend             |
| `frontend:lint`     | Lint the frontend                            |
| `frontend:install`  | Install frontend dependencies                |
| `backend:dev`       | Start Django dev server (requires local venv) |
| `backend:test`      | Run backend tests with pytest                |
| `backend:lint`      | Lint backend with ruff                       |
| `backend:migrate`   | Run Django migrations (local)                |
| `docker:up`         | Start all Docker services                    |
| `docker:down`       | Stop all Docker services                     |
| `docker:logs`       | Tail logs from all Docker services           |
| `docker:migrate`    | Run migrations inside the Docker backend     |

## Documentation

- [Architecture decisions](docs/ARCHITECTURE.md)
- [API & Endpoints](docs/API.md)
- [Permissions & Role Matrix](docs/PERMISSIONS.md)
- Deployment guide (coming soon)
- Runbook (coming soon)

## License

Private — all rights reserved.
