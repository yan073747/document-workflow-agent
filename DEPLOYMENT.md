# Document Workflow Agent Deployment

This project is deployed as two services:

- Backend: FastAPI service from `backend/`
- Frontend: Next.js app from `frontend-next/`

The public demo domain should point to the frontend:

```text
docflow.aiworkbox.cn
```

## Backend: Render Docker Web Service

Recommended first deployment target: Render Web Service with Docker.

Use the repository root that contains this `render.yaml`.

Render will read:

```text
render.yaml
backend/Dockerfile
backend/requirements.txt
```

Backend health check:

```text
GET /health
```

Expected response:

```json
{"status":"ok","service":"multi-agent-office-workflow"}
```

Default demo account:

```text
demo@example.com / demo123456
```

Important environment variables:

```text
DATABASE_PATH=/app/data/workflow.db
UPLOAD_DIR=/app/data/uploads
LLM_PROVIDER=local
JWT_SECRET=<auto generated or strong random string>
TOKEN_EXPIRE_MINUTES=1440
DEMO_USER_EMAIL=demo@example.com
DEMO_USER_PASSWORD=demo123456
ENABLE_CELERY=false
```

For a public interview demo, keep `LLM_PROVIDER=local` first. The app can run the full workflow without an external model key.

## Frontend: Vercel

Create a Vercel project using:

```text
Root Directory: frontend-next
Framework: Next.js
Build Command: npm run build
Output Directory: .next
```

Add this Vercel environment variable after the backend is deployed:

```text
NEXT_PUBLIC_API_BASE_URL=https://<your-render-backend-url>
```

Then bind the custom domain:

```text
docflow.aiworkbox.cn
```

## Alibaba Cloud DNS

After Vercel gives the domain target, add a DNS record in Alibaba Cloud:

```text
Type: CNAME
Host: docflow
Value: <vercel-cname-target>
```

If using another hosting platform for the frontend, follow that platform's CNAME target.

## Smoke Test

After deployment:

1. Open `https://docflow.aiworkbox.cn`.
2. Log in with `demo@example.com / demo123456`.
3. Upload `sample-data/sales_orders.xlsx`.
4. Use this objective:

```text
Analyze the sales order data, identify key regions, top product categories, and operational recommendations, then generate a management report.
```

5. Confirm the generated plan.
6. Verify the report preview and Markdown/PDF download.

## Main Site Switch

After the smoke test passes, update the main site:

```ts
deploymentStatus: "deployed"
```

for the `document-workflow` entry in:

```text
ai-office-toolbox/lib/agent-demos.ts
```
