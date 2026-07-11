# Platform Upgrade Design

## Goal

Upgrade the current multi-agent office workflow demo from a single-page HTML app into a fuller technical showcase with a React/Next.js frontend, richer Excel analytics, authenticated task ownership, and optional Celery/Redis asynchronous execution.

## Scope

This upgrade has three ordered phases:

1. Replace the static frontend with a Next.js application while keeping FastAPI as the backend API.
2. Add a real `.xlsx` sample and expand sales analytics so the UI can render meaningful charts.
3. Add demo-account authentication, task ownership checks, and Celery/Redis execution for confirmed workflow runs.

The existing FastAPI workflow, LangGraph orchestration, local-rule LLM fallback, Markdown/PDF report export, task history, Trace records, and retry flow remain part of the system.

## Phase 1: Next.js Frontend

Create a new `frontend-next/` application instead of deleting the current `frontend/` folder. The current frontend stays as a fallback while the React version is built.

The Next.js app will provide:

- Login screen prepared for the later authentication phase.
- Dashboard with task creation, file upload, metrics, workflow graph, provider status, task history, Trace, report preview, and downloads.
- Task detail view that can load a task by id.
- API client wrapper so backend URL and auth token handling are centralized.
- Recharts dependency reserved for Phase 2 chart rendering.

The backend continues to serve API routes only. Next.js runs separately during development.

## Phase 2: Excel Analytics And Charts

The analyzer will support a richer Excel dataset with these metrics:

- Monthly sales trend.
- Region revenue ranking.
- Category revenue ranking.
- Salesperson revenue ranking.
- Customer type revenue mix.
- Core KPIs: revenue, order count, quantity, average order value.

The `SalesAnalysis` model will add structured chart-ready arrays. The report writer will include the expanded findings in Markdown. The Next.js frontend will show the data as line, bar, and pie charts.

A generated `sample-data/sales_orders.xlsx` file will be committed so the project can demonstrate real Excel input without relying only on CSV.

## Phase 3: Auth, Permissions, Celery/Redis

Authentication will use a demo-friendly email/password flow:

- Built-in demo account: `demo@example.com / demo123456`.
- Optional registration endpoint for additional local users.
- JWT bearer token returned by login.
- Password hashes stored with `passlib`.

Authorization rules:

- Every task has an `owner_id`.
- Task list returns only the current user's tasks.
- Task detail, trace, confirm, retry, and report downloads reject tasks owned by another user.
- Existing unauthenticated tests will be updated to login first.

Asynchronous execution:

- Task creation runs the planning phase synchronously so the user can review the plan immediately.
- Confirming a task enqueues the execution phase through Celery when Redis is configured.
- A local inline fallback remains available when Celery/Redis is not running, so the project stays easy to run.
- The frontend polls task detail and Trace until completion or failure.

## Non-Goals

- No organization or team roles.
- No admin dashboard.
- No WebSocket requirement in this phase.
- No PostgreSQL migration in this phase.
- No replacement of the existing LangGraph workflow internals unless needed for async boundaries.

## Validation

Each phase must pass:

- Backend tests with `python -m pytest -q`.
- Frontend checks with `npm run lint` or the nearest configured equivalent.
- Manual smoke test: create task, confirm plan, view Trace, view charts, download Markdown/PDF.

