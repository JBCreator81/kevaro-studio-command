# Google Cloud runtime configuration

The existing multi-stage `Dockerfile` is the only deployment artifact. It starts the FastAPI service through `python -m studio_command`, reads Cloud Run's `PORT`, and serves the built frontend and API together.

## Required Google Cloud configuration

Use project `kevaro-studio-command`. The Cloud Run runtime service account needs only the existing Firestore/Cloud Storage permissions required by the application and `roles/secretmanager.secretAccessor` on these two secrets:

- `parallel-api-key` — the existing Parallel API credential
- `kevaro-internal-auth-token` — the existing trusted internal mutation credential

Secret values are created or rotated out of band. Do not put values in this repository, build arguments, image environment, deployment manifests, or command history. Secret IDs can be overridden with `KEVARO_PARALLEL_SECRET_ID` and `KEVARO_INTERNAL_AUTH_SECRET_ID`; values cannot.

Set non-secret Cloud Run environment configuration:

```text
KEVARO_RUNTIME_MODE=cloud
GOOGLE_CLOUD_PROJECT=kevaro-studio-command
KEVARO_STUDIO_HEAD_NAME=<authorized judge/demo Studio Head display name>
```

On Cloud Run, application startup reads `latest` for both secret IDs directly through Secret Manager using Application Default Credentials. Missing, empty, inaccessible, or misconfigured secrets abort startup. Cloud mode never falls back to `PARALLEL_API_KEY` or `KEVARO_INTERNAL_AUTH_TOKEN` environment values.

Judge-facing reads may be public, but production-specific access and every mutation use a signed crew session resolved against server-side production assignments. Studio Head-only transitions—including decisions, evidence amendments, selective refresh, and finalization—are authorized on the server. The legacy trusted internal token remains a deployment health boundary; never embed it, a session-signing secret, or an OAuth client secret in frontend bundles.

Verify non-secret readiness with `GET /health`. Its `runtime_configuration` reports Google Cloud, Secret Manager, Parallel credential, and protected mutation boundary as `configured`/`unavailable` or `enabled`/`disabled`; it never returns values.

## Local development

Local mode is the default when `K_SERVICE` is absent. Existing local environment variables remain supported and no Secret Manager request is made:

```text
PARALLEL_API_KEY=<local-only value>
KEVARO_INTERNAL_AUTH_TOKEN=<local-only value>
KEVARO_STUDIO_HEAD_NAME=Studio Head
```

Tests should inject `RuntimeConfig` or a mock secret provider. Setting `KEVARO_RUNTIME_MODE=cloud` intentionally enables fail-closed deployed behavior.
