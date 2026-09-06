# Google Cloud runtime configuration

The existing multi-stage `Dockerfile` is the only deployment artifact. It starts the FastAPI service through `python -m studio_command`, reads Cloud Run's `PORT`, and serves the built frontend and API together.

## Required Google Cloud configuration

Use project `kevaro-studio-command`. The Cloud Run runtime service account needs only the existing Firestore/Cloud Storage permissions required by the application and `roles/secretmanager.secretAccessor` on these four existing secret resources:

- `parallel-api-key` — the Parallel API credential
- `kevaro-internal-auth-token` — the trusted internal mutation credential
- `kevaro-session-signing-secret` — the signed crew-session key
- `kevaro-google-oauth-client-id` — the Google OAuth client identifier injected by secret reference

Secret values are created or rotated out of band. Do not put values in this repository, build arguments, image environment, deployment manifests, or command history. Secret IDs can be overridden with `KEVARO_PARALLEL_SECRET_ID` and `KEVARO_INTERNAL_AUTH_SECRET_ID`; values cannot.

Set non-secret Cloud Run environment configuration:

```text
KEVARO_RUNTIME_MODE=cloud
GOOGLE_CLOUD_PROJECT=kevaro-studio-command
KEVARO_STUDIO_HEAD_NAME=<authorized judge/demo Studio Head display name>
KEVARO_GOOGLE_AUTH_CLIENT_ID=<Secret Manager reference: kevaro-google-oauth-client-id:latest>
```

On Cloud Run, application startup reads `latest` for the Parallel, internal-auth, and session-signing secret IDs directly through Secret Manager using Application Default Credentials. Cloud Run injects the OAuth client identifier from its existing secret reference. Missing, empty, inaccessible, or misconfigured values abort startup. Cloud mode never falls back to local credential environment values.

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

## Verified public target

The intended service is `kevaro-studio-command` in `northamerica-northeast1` using `kevaro-studio-runtime@kevaro-studio-command.iam.gserviceaccount.com`. Its canonical URL is:

```text
https://kevaro-studio-command-1016343355645.northamerica-northeast1.run.app
```

Deployment verification must confirm that `/health` reports configured cloud, Secret Manager, Parallel, mutation-auth, and crew-session boundaries; `/api/studio-snapshot` returns `bootstrap_source: GOVERNED_RUNTIME`; anonymous production-specific reads and mutations return 401; and an authenticated finalization attempt remains subject to current clearance, QA, readiness, and evidence gates.
