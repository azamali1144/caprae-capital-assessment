# Deployment

```
Vercel (Next.js, static + SSR at the edge)
   │  HTTPS
   ▼
Cloud Run  leadlens-api  (container, scale 0 → 3, CPU always allocated)
   ├── Neon Postgres   (serverless)
   └── Upstash Redis   (serverless, TLS - rediss://)
```

Cloud provider: **GCP** (Cloud Run, Artifact Registry, Secret Manager).
Everything else is managed/serverless, so there's nothing to patch and the
whole thing costs ~$0 when nobody's using it.

Why "CPU always allocated" (`--no-cpu-throttling`): enrichment runs as a
background task after the import request returns. With the default throttling
Cloud Run would pause the CPU as soon as the response is sent and the job would
crawl at a snail's pace. The bigger-scale fix is moving jobs to an ARQ worker
(see README → roadmap).

## 1. Data services

**Neon** - create a project, copy the **direct** (not `-pooler`) connection
string and change the driver prefix. asyncpg caches prepared statements, which
doesn't play well with PgBouncer's transaction pooling - and SQLAlchemy already
keeps its own small pool, so the direct endpoint is the simpler choice here.

```
postgresql+asyncpg://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/leadlens?ssl=require
```

**Upstash** - create a Redis database in the same region, copy the `rediss://` URL.

Store both in Secret Manager:

```bash
gcloud config set project YOUR_PROJECT
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

printf '%s' 'postgresql+asyncpg://...'  | gcloud secrets create leadlens-database-url --data-file=-
printf '%s' 'rediss://default:...@...'  | gcloud secrets create leadlens-redis-url --data-file=-
```

## 2. Backend → Cloud Run

One-off from your machine:

```bash
REGION=us-central1
gcloud artifacts repositories create leadlens --repository-format=docker --location=$REGION

cd backend
gcloud builds submit --tag $REGION-docker.pkg.dev/YOUR_PROJECT/leadlens/api:v1

gcloud run deploy leadlens-api \
  --image $REGION-docker.pkg.dev/YOUR_PROJECT/leadlens/api:v1 \
  --region $REGION --allow-unauthenticated \
  --no-cpu-throttling --min-instances 0 --max-instances 3 --memory 1Gi \
  --set-env-vars CORS_ORIGINS=https://YOUR-APP.vercel.app \
  --set-secrets DATABASE_URL=leadlens-database-url:latest,REDIS_URL=leadlens-redis-url:latest
```

The container runs `alembic upgrade head` before starting uvicorn, so the
schema is created on first boot. Check it: `curl https://<run-url>/api/v1/health`.

Give the Cloud Run service account access to the two secrets
(`roles/secretmanager.secretAccessor`) if the deploy complains.

### Auto-deploy from GitHub (optional)

`.github/workflows/deploy-backend.yml` redeploys on every push to `main` that
touches `backend/`. It uses Workload Identity Federation (no JSON keys) and
stays switched off until these **repo variables** exist:

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `leadlens-demo` |
| `GCP_REGION` | `us-central1` |
| `GCP_WIF_PROVIDER` | `projects/123/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_DEPLOY_SA` | `deployer@leadlens-demo.iam.gserviceaccount.com` |
| `FRONTEND_ORIGIN` | `https://leadlens.vercel.app` |

## 3. Frontend → Vercel

1. Import the GitHub repo in Vercel, set **Root Directory** to `frontend`.
2. Env var: `NEXT_PUBLIC_API_URL=https://<cloud-run-url>/api/v1`
3. Deploy. Every PR gets a preview URL; `main` goes to production.
4. Put the Vercel URL into the backend's `CORS_ORIGINS` (redeploy the api).

## 4. Demo data

```bash
# against the production db, from your machine
cd backend
DATABASE_URL='postgresql+asyncpg://...' REDIS_URL='rediss://...' \
  uv run python -m scripts.seed_demo
```

## Review week tip

Neon and Cloud Run both scale to zero, so the first request after a quiet
period takes a few seconds. For the week the demo is being reviewed, set
`--min-instances 1` on the api to keep it warm.
