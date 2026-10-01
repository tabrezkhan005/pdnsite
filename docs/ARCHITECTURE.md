# Architecture Decisions

This document records key architectural decisions for the Perin Devi Natyalayam project.

## Monorepo layout

- **frontend/** — Next.js 16 with TypeScript, App Router, and Tailwind CSS v4.
- **backend/** — Django 5.x with Django REST Framework. API-only; no server-rendered HTML.
- **infra/** — Docker, nginx, and deployment configurations.
- **docs/** — Architecture, deployment, and runbook documentation.

The frontend and backend are separate deployable units. In production they will live on sibling subdomains (e.g. `app.pdn.example.com` and `api.pdn.example.com`).

## Technology choices

| Layer        | Technology                | Rationale                                       |
| ------------ | ------------------------- | ----------------------------------------------- |
| Frontend     | Next.js 16 (App Router)   | Server components, ISR, excellent DX            |
| Styling      | Tailwind CSS v4           | Already configured in the starter project       |
| Backend      | Django + DRF              | Mature, batteries-included, strong admin        |
| Database     | PostgreSQL 16             | ACID, JSON support, excellent Django integration |
| Cache/Broker | Redis                     | Celery broker + general caching                 |
| Task queue   | Celery + django-celery-beat | Reliable async tasks and periodic scheduling   |
| API docs     | drf-spectacular (OpenAPI) | Auto-generated schema, Swagger UI               |
| Auth         | Session-based (cookies)   | Simpler than JWT for same-site SPA + API        |

## Money convention

**All monetary amounts are stored as integer paise (1/100 of INR), never as floats.**

- `amount_paise = 50000` means ₹500.00
- Display formatting is a presentation concern handled in serializers and the frontend.
- This avoids floating-point precision errors in calculations.

## Timezone convention

- **Storage**: All datetimes are stored in UTC (`USE_TZ = True`).
- **Display**: `TIME_ZONE = 'Asia/Kolkata'` for admin and default rendering.
- **Frontend**: Receives UTC from the API and formats to the user's locale.

## Authentication

- Session authentication with secure, HTTP-only, same-site cookies.
- CSRF protection enabled (Django default).
- CORS and CSRF trusted origins configured via environment variables.
- Future: role-based access (ADMIN, STAFF, STUDENT, GUARDIAN).

## UUID primary keys

All models use UUID primary keys for security (non-enumerable) and distributed-system friendliness.

## Soft delete pattern

A `SoftDeleteModel` mixin provides `is_deleted` and `deleted_at` fields with a custom manager that filters out soft-deleted records by default. Hard-delete is still possible via `hard_delete()`.

## File storage

- **Development**: Local filesystem (`MEDIA_ROOT`).
- **Production**: S3-compatible storage via `django-storages` and `boto3`, configured with environment variables.

## API versioning

APIs are versioned under `/api/v1/`. Breaking changes will increment the version number.
