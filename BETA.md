# Nexus AI Beta Release

## Release gate

A beta release is ready only when all of these are true:

- `python -m pytest -q` is green on `main`.
- The production Docker image builds successfully.
- The container smoke test reaches `/health` and reports `status=ok`.
- No real secrets are committed. Use environment variables or the deployment secret store.
- Beta releases are published from a version tag such as `v0.1.0`.

## Local beta run

1. Copy `.env.example` to `.env` and add only local credentials.
2. Run `docker compose up --build -d`.
3. Verify `http://localhost:8000/health` returns an OK status.
4. Open the web interface at `http://localhost:8000/ui`.
5. Stop the stack with `docker compose down`.

## Release

Push a semantic version tag (`vMAJOR.MINOR.PATCH`). The release workflow builds the production image and publishes both the version tag and `beta` tag to GitHub Container Registry.

## Rollback

Deploy the previous known-good version tag. Do not mutate the `beta` tag manually during an incident; publish a new corrective version after tests pass.
