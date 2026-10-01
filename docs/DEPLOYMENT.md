# Deployment Guide (Railway)

This repository is configured as a monorepo for seamless deployment on [Railway](https://railway.app/).

## Services Architecture

The production environment consists of 5 services:
1. **PostgreSQL** (Database)
2. **Redis** (Cache & Celery Broker)
3. **Backend API** (Django Gunicorn)
4. **Celery Worker** (Background Tasks)
5. **Frontend Web** (Next.js)

---

## 1. Provision Databases
In your Railway Project:
1. Click **New** -> **Database** -> **Add PostgreSQL**
2. Click **New** -> **Database** -> **Add Redis**

## 2. Deploy Backend API
1. Click **New** -> **GitHub Repo** -> select this repository.
2. In the deployment settings, set the **Root Directory** to `/backend`.
3. Railway will automatically detect the `Dockerfile` and `railway.toml`.
4. Add the following Environment Variables:
   - `DJANGO_SETTINGS_MODULE`: `config.settings.production`
   - `DJANGO_SECRET_KEY`: (Generate a secure key)
   - `DATABASE_URL`: `${{Postgres.DATABASE_URL}}`
   - `REDIS_URL`: `${{Redis.REDIS_URL}}`
   - `CELERY_BROKER_URL`: `${{Redis.REDIS_URL}}`
   - `CORS_ALLOWED_ORIGINS`: `https://your-frontend-domain.up.railway.app`
   - `CSRF_TRUSTED_ORIGINS`: `https://your-frontend-domain.up.railway.app`
5. Deploy.

## 3. Deploy Celery Worker
1. Click **New** -> **GitHub Repo** -> select this repository again.
2. Set the **Root Directory** to `/backend`.
3. **Important:** Override the Start Command in Settings:
   ```bash
   celery -A config worker --loglevel=info
   ```
4. Copy the exact same environment variables from the Backend API service.
5. Deploy.

## 4. Deploy Frontend (Next.js)
1. Click **New** -> **GitHub Repo** -> select this repository again.
2. Set the **Root Directory** to `/frontend`.
3. Add the following Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend-domain.up.railway.app/api`
4. Deploy.

---

## CI/CD
GitHub Actions is configured in `.github/workflows/ci.yml`. 
Every push to `main` runs:
- Backend: Ruff linting and Pytest.
- Frontend: ESLint and Next.js production build check.

Railway will automatically deploy on pushes to `main` if connected.
