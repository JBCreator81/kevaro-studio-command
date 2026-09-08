# Governed final-media registration runbook

Do not register placeholders. For each completed export listed in `FINAL_DELIVERABLE_MANIFEST.json`:

1. Calculate SHA-256 and capture a media probe showing duration, dimensions, aspect ratio, container, codecs, frame rate, and audio stream properties.
2. Update only the matching manifest record with observed values and creation provenance; retain the required values separately.
3. Authenticate as the assigned asset owner or Studio Head and call the existing production-specific asset registration endpoint with category `VIDEO`, the canonical production identity, file bytes, checksum/probe provenance, expected deliverable, acceptance criteria, and clearance state `PENDING_FINAL_CONTENT_REVIEW`.
4. Submit the immutable registered version for review through `/assets/{asset_id}/submit-review`.
5. Have the authorized Clearance/Compliance and independent QA roles record their separate dispositions; the creator must not self-certify.
6. Use governed state transitions to refresh clearance, QA, readiness, and decision artifacts. Never edit Firestore directly.

Client Instagram/YouTube credentials are outside Kevaro and are not required to create or clear the production package.
