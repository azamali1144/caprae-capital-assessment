# Deployment

Everything runs on **GCP** - two Cloud Run services plus managed data services.

```
Browser
   │  HTTPS
   ▼
Cloud Run  leadlens-web  (Next.js standalone container, scale 0 → 3)
   │  REST (browser → api)
   ▼
Cloud Run  leadlens-api  (FastAPI container, scale 0 → 3, CPU always allocated)
   ├── Neon Postgres   (serverless)
   └── Upstash Redis   (serverless, TLS - rediss://)
```

Cloud provider: **GCP** (Cloud Run, Artifact Registry, Secret Manager).
One cloud, one way of deploying (a container per service), nothing to patch,
and it costs ~$0 when nobody's using it.

Why "CPU always allocated" on the api (`--no-cpu-throttling`): enrichment runs
as a background task after the import request returns. With the default
throttling Cloud Run would pause the CPU as soon as the response is sent and the
job would crawl at a snail's pace. The bigger-scale fix is moving jobs to an ARQ
worker (see README → roadmap). The web service doesn't need it.

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
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com

printf '%s' 'postgresql+asyncpg://...'  | gcloud secrets create leadlens-database-url --data-file=-
printf '%s' 'rediss://default:...@...'  | gcloud secrets create leadlens-redis-url --data-file=-
```

## 2. Backend → Cloud Run (`leadlens-api`)

```bash
REGION=us-central1
REPO=$REGION-docker.pkg.dev/YOUR_PROJECT/leadlens
gcloud artifacts repositories create leadlens --repository-format=docker --location=$REGION

cd backend
gcloud builds submit --tag $REPO/api:v1

gcloud run deploy leadlens-api \
  --image $REPO/api:v1 \
  --region $REGION --allow-unauthenticated \
  --no-cpu-throttling --min-instances 0 --max-instances 3 --memory 1Gi \
  --set-secrets DATABASE_URL=leadlens-database-url:latest,REDIS_URL=leadlens-redis-url:latest
```

The container runs `alembic upgrade head` before starting uvicorn, so the
schema is created on first boot. Note the service URL it prints
(`https://leadlens-api-xxxx.a.run.app`) and check it:
`curl https://<api-url>/api/v1/health`.

Give the Cloud Run service account access to the two secrets
(`roles/secretmanager.secretAccessor`) if the deploy complains.

## 3. Frontend → Cloud Run (`leadlens-web`)

`NEXT_PUBLIC_API_URL` is baked into the browser bundle at build time, so it's a
build argument:

```bash
cd frontend
gcloud builds submit --config - . <<EOF
steps:
  - name: gcr.io/cloud-builders/docker
    args: ["build", "--build-arg", "NEXT_PUBLIC_API_URL=https://<api-url>/api/v1", "-t", "$REPO/web:v1", "."]
images: ["$REPO/web:v1"]
EOF

gcloud run deploy leadlens-web \
  --image $REPO/web:v1 \
  --region $REGION --allow-unauthenticated \
  --port 3000 --min-instances 0 --max-instances 3 --memory 512Mi
```

Then let the api accept requests from the web service's URL:

```bash
gcloud run services update leadlens-api --region $REGION \
  --update-env-vars CORS_ORIGINS=https://<web-url>
```

Want a nicer address than `*.run.app`? `gcloud beta run domain-mappings create`
maps your own domain to either service.

## 4. Auto-deploy from GitHub (optional)

`.github/workflows/deploy-backend.yml` and `deploy-frontend.yml` rebuild and
redeploy on every push to `main` that touches `backend/` or `frontend/`. They
use Workload Identity Federation (no JSON keys) and stay switched off until
these **repo variables** exist:

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `leadlens-demo` |
| `GCP_REGION` | `us-central1` |
| `GCP_WIF_PROVIDER` | `projects/123/locations/global/workloadIdentityPools/github/providers/github` |
| `GCP_DEPLOY_SA` | `deployer@leadlens-demo.iam.gserviceaccount.com` |
| `API_URL` | `https://leadlens-api-xxxx.a.run.app` |
| `FRONTEND_ORIGIN` | `https://leadlens-web-xxxx.a.run.app` |

## 5. Demo data

```bash
# against the production db, from your machine
cd backend
DATABASE_URL='postgresql+asyncpg://...' REDIS_URL='rediss://...' \
  uv run python -m scripts.seed_demo
```

## Review week tip

Neon and Cloud Run both scale to zero, so the first request after a quiet
period takes a few seconds. For the week the demo is being reviewed, set
`--min-instances 1` on both services to keep them warm.
