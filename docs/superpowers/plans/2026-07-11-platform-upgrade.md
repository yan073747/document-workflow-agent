# Platform Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the multi-agent office workflow project with a Next.js frontend, richer Excel analytics and charts, demo-account authentication, task ownership, and Celery/Redis async execution.

**Architecture:** Keep FastAPI as the backend API and add a separate `frontend-next/` Next.js app. Extend backend data models first, then make frontend consume the richer API. Add auth and task ownership before Celery so async workers operate on already-scoped task records.

**Tech Stack:** FastAPI, LangGraph, SQLite, Celery, Redis, Next.js, React, TypeScript, Recharts, JWT, passlib.

## Global Constraints

- Keep the existing local-rule LLM fallback.
- Keep Markdown/PDF report download endpoints.
- Keep the old `frontend/` folder until the Next.js app is verified.
- Use demo account mode with `demo@example.com / demo123456`.
- Keep an inline execution fallback when Celery/Redis is not configured.
- Preserve a clean technical-showcase README tone.

---

## File Structure

- Create `frontend-next/`: Next.js application, API client, dashboard components, charts, login screen.
- Modify `backend/app/core/models.py`: add auth models and chart-ready sales analysis models.
- Modify `backend/app/db/repository.py`: add users table, owner-aware task queries, and migration-safe column additions.
- Modify `backend/app/main.py`: add auth endpoints, dependency-based current user, owner checks, and async enqueue hooks.
- Modify `backend/app/services/sales_analyzer.py`: compute expanded analytics.
- Modify `backend/app/services/report_renderer.py`: include expanded analytics in Markdown.
- Create `backend/app/services/auth.py`: password hashing, token creation, token verification.
- Create `backend/app/services/task_runner.py`: inline/Celery dispatch facade.
- Create `backend/app/worker.py`: Celery app and execution task.
- Modify `backend/tests/`: update tests for auth, ownership, charts, and async fallback.
- Create `sample-data/sales_orders.xlsx`: real Excel sample matching the supported schema.
- Modify `README.md`: document Next.js, auth demo account, richer Excel sample, and Celery/Redis.

---

### Task 1: Add Next.js Frontend Shell

**Files:**
- Create: `frontend-next/package.json`
- Create: `frontend-next/next.config.js`
- Create: `frontend-next/tsconfig.json`
- Create: `frontend-next/src/app/layout.tsx`
- Create: `frontend-next/src/app/page.tsx`
- Create: `frontend-next/src/app/globals.css`
- Create: `frontend-next/src/lib/api.ts`
- Create: `frontend-next/src/components/Dashboard.tsx`

**Interfaces:**
- Consumes: existing FastAPI endpoints under `/api`.
- Produces: a running React dashboard at `http://localhost:3000`.

- [ ] Create the Next.js project files with TypeScript and Recharts dependencies.
- [ ] Implement `api.ts` with `API_BASE`, `apiGet`, `apiPostForm`, and `downloadReportUrl`.
- [ ] Port the current dashboard behavior into React state.
- [ ] Run `npm install`.
- [ ] Run `npm run lint` or `npm run typecheck`.
- [ ] Manually smoke test task creation, confirmation, history, Trace, and report downloads.

### Task 2: Add Rich Excel Analytics

**Files:**
- Modify: `backend/app/core/models.py`
- Modify: `backend/app/services/sales_analyzer.py`
- Modify: `backend/app/services/report_renderer.py`
- Modify: `backend/tests/test_workflow.py`
- Create: `backend/tests/test_sales_analyzer.py`
- Create: `sample-data/sales_orders.xlsx`

**Interfaces:**
- Produces: `SalesAnalysis.monthly_trend`, `region_ranking`, `category_ranking`, `salesperson_ranking`, and `customer_type_mix`.
- Consumes: CSV/XLSX files with the existing sales columns.

- [ ] Write analyzer tests for monthly trend, salesperson ranking, and XLSX loading.
- [ ] Extend Pydantic models with chart-ready metric classes.
- [ ] Update `analyze_sales_file` to compute expanded metrics.
- [ ] Update Markdown report generation with trend and ranking sections.
- [ ] Generate `sample-data/sales_orders.xlsx` from representative sales rows.
- [ ] Run `python -m pytest backend/tests/test_sales_analyzer.py backend/tests/test_workflow.py -q`.

### Task 3: Render Charts In Next.js

**Files:**
- Modify: `frontend-next/src/components/Dashboard.tsx`
- Create: `frontend-next/src/components/AnalyticsCharts.tsx`
- Modify: `frontend-next/src/app/globals.css`

**Interfaces:**
- Consumes: expanded `task.analysis` from Task 2.
- Produces: line chart, bar charts, pie chart, and KPI cards.

- [ ] Add TypeScript types for expanded `SalesAnalysis`.
- [ ] Build `AnalyticsCharts` with Recharts.
- [ ] Show charts only when task analysis exists.
- [ ] Keep empty state text for tasks waiting on confirmation.
- [ ] Run frontend typecheck/lint.
- [ ] Smoke test using `sample-data/sales_orders.xlsx`.

### Task 4: Add Demo Auth And Task Ownership

**Files:**
- Create: `backend/app/services/auth.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/models.py`
- Modify: `backend/app/db/repository.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api.py`
- Create: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`.
- Changes: task routes require `Authorization: Bearer <token>`.
- Consumes: demo account `demo@example.com / demo123456`.

- [ ] Add tests for login success, login failure, current user, and task isolation.
- [ ] Add users table and seed demo user during repository initialization.
- [ ] Add `owner_id` to tasks with migration-safe `ALTER TABLE`.
- [ ] Add auth service for password hashing and JWT.
- [ ] Add FastAPI auth dependencies and protect task routes.
- [ ] Update frontend API client to store and send bearer token.
- [ ] Add login UI to Next.js app.
- [ ] Run backend tests and frontend checks.

### Task 5: Add Celery/Redis Async Execution With Inline Fallback

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/task_runner.py`
- Create: `backend/app/worker.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api.py`
- Create: `backend/tests/test_task_runner.py`
- Modify: `README.md`

**Interfaces:**
- Produces: Celery worker command `celery -A app.worker.celery_app worker --loglevel=info`.
- Changes: confirm route enqueues execution when Celery is enabled, otherwise executes inline.
- Consumes: `REDIS_URL`, `ENABLE_CELERY`.

- [ ] Add tests proving inline fallback completes tasks without Redis.
- [ ] Add settings for Celery enablement and Redis URL.
- [ ] Add task runner facade with `run_execution(task_id)` and `enqueue_execution(task_id)`.
- [ ] Add Celery app and worker task.
- [ ] Update confirm route to call the runner.
- [ ] Update Next.js polling after confirmation.
- [ ] Document Redis startup, worker startup, and fallback mode.
- [ ] Run `python -m pytest -q` and frontend checks.

### Task 6: Final Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/screenshots/README.md`

**Interfaces:**
- Produces: updated local run guide and screenshot checklist.

- [ ] Update README with Next.js run commands, demo login, XLSX sample, and Celery/Redis commands.
- [ ] Update architecture doc with frontend/backend/worker boundaries.
- [ ] Run full backend tests.
- [ ] Run frontend checks.
- [ ] Start backend and Next.js dev server for manual smoke test.
- [ ] Commit and push all changes.

