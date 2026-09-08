# Three-minute governed demo

Use the authenticated live application and select **Aurelian Parallel E2E Certification 20260903-B**. Do not use `frontend/public/studio-snapshot.json`; the header must show **LIVE PRODUCTION** and bootstrap must report `GOVERNED_RUNTIME`. Production-specific views require an assigned Crew Identity. Anonymous protected reads and actions are expected to be rejected.

## 0:00–0:30 — Governed production truth

Show the exact production identity, readiness 100, Studio Head decision `APPROVED`, and final status `READY_FOR_DELIVERY`. Point out Crew Identity and the Studio Head authority gate.

## 0:30–1:05 — Gemini, Google ADK, and Parallel evidence

Show the Gemini-backed Google ADK production graph. Open Research / the Parallel Evidence Room and show `Parallel · VERIFIED`, the research objective, persisted citations, search metadata, evidence gaps, provenance, and evidence-to-production impact. Explain that credentials are never returned to the browser.

## 1:05–1:40 — Governed graph and Node Intelligence

Show the governed agent graph, parallel scheduling and asset/media branches, and Node Intelligence. In Production Memory, show the verified evidence amendment, its authoritative Aurelian source artifact, and the appended artifact-refresh event. Emphasize that the original Studio Head decision was not rewritten.

## 1:40–2:15 — Evidence Before Execution

Show the three registered immutable final VIDEO assets for Instagram Reels, YouTube Shorts, and the 16:9 master. Show their hashes and provenance, Clearance `PASS`, distinct independent QA `PASS`, and readiness 100.

## 2:15–2:40 — Human authority and finalization

Show Studio Head decision sequence 2 as `APPROVED`, finalization complete, the persisted final package, and `READY_FOR_DELIVERY`. Do not repeat finalization or rewrite any governed record.

## 2:40–3:00 — Runtime and access boundary

Show the healthy deployed public runtime and `bootstrap_source: GOVERNED_RUNTIME`. Show that the authenticated assigned-crew view resolves the Aurelian production. Demonstrate only with a legitimate assigned session; anonymous protected operations remain rejected. Close on the governed chain: **Evidence → Decision → Execution**.

## Local run and checks

```bash
python -m studio_command
cd frontend && npm run dev
```

For the production build, run `npm run build` in `frontend/`; the FastAPI service serves `frontend/dist`. Cloud configuration and credential boundaries are documented in `docs/deployment/GOOGLE_CLOUD_RUNTIME.md`.

## Pre-recording certification check

Confirm `/health` reports the certified deployed revision and `/api/studio-snapshot` reports the exact Aurelian identity with `GOVERNED_RUNTIME`. With a legitimate assigned crew session, confirm `FINAL_MEDIA_APPROVED`, readiness 100, `READY_FOR_DELIVERY`, all three delivery artifacts, Node Intelligence, provenance, and Parallel evidence. If an assigned session is unavailable, do not bypass authentication or present the static fallback as live proof.
