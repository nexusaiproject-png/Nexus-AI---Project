# Nexus AI Production Deployment

## Goal
Run Nexus AI as a production FastAPI service behind HTTPS with persistent application data and health checks.

## Required external accounts
1. A cloud host that can run the repository Docker image.
2. A DNS/domain provider.
3. A production database/storage service when scaling beyond the single-node deployment.
4. Production secrets supplied through the cloud provider's secret/environment settings, never committed to Git.

## Container contract
- Build: `docker build -t nexus-ai .`
- Port: `8000`
- Health: `GET /health`
- Container user: `nexus` (non-root)
- Entrypoint: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Local persistent volume: `/app/data`

The repository CI already builds the production image and performs an HTTP health smoke test.

## Environment
Set these values privately in the production environment:
- `NEXUS_ENV=production`
- `NEXUS_PUBLIC_URL=https://YOUR_DOMAIN`
- `NEXUS_COOKIE_SECURE=true`
- `NEXUS_EXPOSE_DEV_TOKENS=false`
- Stripe secret/webhook/price identifiers as required by billing

Never place production secrets in GitHub source files.

## Deployment sequence
1. Create the cloud application from this GitHub repository.
2. Configure it to build from `Dockerfile`.
3. Expose container port `8000`.
4. Configure environment variables/secrets.
5. Configure health check path `/health`.
6. Deploy from `main`.
7. Point domain DNS to the cloud service.
8. Enable managed TLS/HTTPS.
9. Verify `GET /health` returns HTTP 200 and `status=ok`.
10. Open `/ui` and verify the responsive workspace.
11. Run signup/login, billing, integration, security, and backup smoke tests against production.

## Important production limitation
The current repository has a local application data volume for single-node deployment. Before horizontal scaling or high-volume production, move durable state to managed external database/storage and configure automated backups and restore tests. Do not treat an ephemeral cloud filesystem as durable storage.

## Rollback
Deployments must be versioned by Git commit. If a release fails health checks or smoke tests, roll back to the previous known-good commit/image.
