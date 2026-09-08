# Kevaro Studio Command

**One Studio Head. A governed production crew of humans and agents.**

Kevaro Studio Command is an AI-native production command system for film, television, advertising, branded content, and creative-production teams.

It turns a production directive into researched, coordinated, verified, human-governed work using Gemini, Google Agent Development Kit, Google Cloud, and Parallel.

> **Not just a single source of truth. A single source of action.**

## What Kevaro Does

A Studio Head issues a production directive.

Kevaro coordinates specialist agents and human production roles across:

- production strategy
- research and evidence
- creative development
- production planning
- scheduling
- asset and media coordination
- rights and clearance
- independent verification and QA
- human approval
- change impact
- final delivery

The governing flow is:

**Evidence → Decision → Execution**

Human authority remains intact while routine coordination and production work move forward autonomously where appropriate.

## Why It Exists

Creative teams already use tools for writing, editing, scheduling, review, assets, communication, and delivery.

The missing layer is often the one that answers:

- What should happen next?
- Who owns it?
- What evidence supports the decision?
- What changed?
- Which work is still valid?
- What needs human approval?
- What can safely proceed automatically?
- Who changed or approved something?
- Is the production actually ready?

Kevaro Studio Command is designed to become that production-command layer.

## Core Principles

- **Evidence Before Execution**
- **Build a graph, not a chain**
- Human approval only where it adds value
- Execution agents cannot verify their own work
- Real tool use, not simulated autonomy
- Explicit production state transitions
- Persistent production memory
- Auditability and provenance
- Preserve unaffected work during change
- Least-privilege work ownership
- Role-aware guidance
- Near-zero-training usability
- Premium cinematic UX
- Authentic production terminology
- Learn continuously, change deliberately

## Governed Production Graph

The current architecture coordinates specialist production functions including:

- Executive Producer / Orchestrator
- Research Agent
- Creative Development Agent
- Production Manager Agent
- Scheduling Agent
- Asset & Media Agent
- Clearance & Compliance Agent
- Independent Verification / QA Agent
- Studio Head Decision Gate

Work that can safely happen in parallel is allowed to branch.

Dependencies reconverge only where required.

The system is intentionally designed as a **production graph**, not a simple linear agent chain.

## Human Authority

The Studio Head retains final authority over material production decisions.

Supported decision states include:

- `APPROVE`
- `APPROVE WITH CONDITIONS`
- `REQUEST CHANGES`
- `REJECT`

Studio Head attention is treated as a limited production resource.

Routine technical choices should remain with the responsible specialist when they do not materially affect:

- creative intent
- scope
- budget
- schedule
- quality threshold
- rights or legal exposure
- safety
- explicit delivery requirements

Corrective work must pass independent re-verification before returning to the Studio Head.

## Parallel Evidence Room

Parallel is a runtime evidence layer inside Kevaro, not a decorative integration.

Research surfaces are designed to expose:

- research objective
- real sources
- citations
- provenance
- relevance
- uncertainty
- evidence gaps
- unresolved questions
- evidence freshness
- downstream decisions influenced by research

The goal is to make the path from **evidence to production decision** visible.

## Production Memory

Kevaro preserves production truth across the lifecycle.

Production Memory can include:

- production briefs
- research packets
- creative treatments
- production plans
- schedules
- asset and media plans
- clearance records
- QA results
- human decisions
- corrective work
- active conditions
- approved artifacts
- known-good recovery states
- delivery packages
- production history

This persistent state is intended to function as a living **Production Bible**.

## Reality Shift

Production reality changes constantly.

A deadline moves. A deliverable changes. A location becomes unavailable. A budget changes. A legal issue appears.

Kevaro's Reality Shift / Change Impact model determines what that change affects.

It can identify:

- work that remains valid
- work that becomes stale
- work that must reopen
- approvals that become invalid
- evidence that must refresh
- clearance that must rerun
- QA that must rerun
- scheduling consequences
- delivery consequences

The governing rule is:

> **Do not restart unaffected work.**

Known-good work should be preserved.

## Full Node Intelligence

The Live Production Graph is not intended to be only a status visualization.

Each node should expose the real governed production artifact behind it.

Examples include:

### Production Brief
Objective, audience, deliverables, constraints, budget, deadline, assumptions, approvals.

### Research
Parallel evidence, sources, findings, provenance, confidence, unresolved questions, decision impact.

### Creative Development
Treatment, concept, tone, messaging, visual direction, references, risks, approvals.

### Production Planning
Tasks, owners, dependencies, requirements, blockers, budget implications, completion criteria.

### Scheduling
Scheduled work, dependencies, parallel groups, critical path, buffers, approval windows, deadline risks.

### Asset & Media
Required assets, sourcing, licensing, formats, missing items, media risks, delivery requirements.

### Clearance & Compliance
Rights status, clearance checks, blocked items, restrictions, unresolved questions, legal risks, next actions.

### Verification QA
Checks performed, failures, unresolved items, conflicts, technical validation, evidence validation, readiness score.

### Studio Head Decision
Recommendation, rationale, material blockers, required human decisions, conditions, authorization state, decision history.

### Final Package
Approved deliverables, evidence, QA, governance record, readiness, delivery status, final production notes.

## Production Accountability

Important production work should identify both human and agent responsibility.

Relevant metadata can include:

- human owner
- responsible AI agent
- contributors
- reviewer / verifier
- approved by
- last changed by
- timestamp
- status
- action history
- decision history

The purpose is professional accountability and collaboration, not opaque employee surveillance.

## Work Ownership & Access Control

Kevaro follows a simple production rule:

> **Read what you need. Edit what you own. Approve only what your role permits. Studio Head governs everything.**

### Studio Head
Full production-wide visibility and governance.

### Assigned Owner
May edit owned work within workflow rules.

### Contributor
May edit only specifically assigned sections or deliverables.

### Reviewer / Verifier
May review, comment, verify, approve, or return work where authorized, but should not silently rewrite creator work.

### Downstream Worker
May read approved dependencies required for their work without modifying upstream artifacts.

### Unassigned Crew
Limited or no edit access.

Changes to completed or approved work owned by someone else should move through governed change control / Reality Shift.

## Role-Aware Guidance

Kevaro should reduce the need for formal software training.

A user entering a production should be able to understand:

- their role
- their assigned work
- what is waiting on them
- what they can edit
- what they can only view
- what context they should review
- what evidence or files are missing
- what action they should take next
- what happens after completion
- when something must be escalated

Guidance depth may include:

- Guided
- Standard
- Expert

A long-term product metric is:

**Time-to-Productive-Work**

The goal is for a newly invited employee, contractor, freelancer, or temporary crew member to begin the correct work within minutes.

## Production Accountability Chain

**Crew Identity → Work Ownership → Scoped Access → Role-Aware Guidance → Node Intelligence → Evidence → Verification → Human Approval → Audit Trail → Final Delivery**

Reality Shift overlays this chain by determining which existing work remains trustworthy when production conditions change.

## Independent Verification

Execution and verification remain separated.

Kevaro's QA model is designed to:

- evaluate artifacts against defined criteria
- identify defects and contradictions
- check cross-artifact consistency
- validate technical requirements
- validate evidence where applicable
- route failed work back for correction
- independently re-check corrected work

An executing agent should not certify its own work.

## Final Production Package

A completed production should resolve into a professional governed package containing relevant:

- approved creative
- production plan
- schedule
- evidence
- assets
- clearance state
- QA results
- human decision record
- production history
- delivery information
- readiness state

The final experience is designed around a clear:

**READY FOR DELIVERY**

state.

## Current Proven Capabilities

The project has already demonstrated:

- live Gemini runtime
- Google ADK orchestration
- Parallel Search runtime
- governed multi-agent production workflow
- parallel production branches
- Studio Head decision gate
- authority calibration
- independent QA
- clearance and compliance flow
- human decision persistence
- approved-artifact persistence
- governed runtime persistence
- final package generation
- `READY_FOR_DELIVERY`
- certified lifecycle readiness score of 100 in controlled testing
- Reality Shift preservation and stale-work propagation
- authenticated, exact-condition evidence amendment with production-linked provenance
- graph-ordered selective artifact refresh with one-document atomic installation
- fail-closed finalization when clearance, QA, or evidence gates remain unresolved
- frontend rendering of production state
- Live Production Graph
- Human Authority Gate
- Node Intelligence backend artifact contract
- production frontend build

## Current Certification Snapshot

The current Aurelian certification production demonstrates the complete governed path from fail-closed evidence collection through immutable media registration, separated review, human approval, and finalization. A Studio Head used persisted production-linked evidence to reconcile one exact platform condition. Kevaro preserved the original decision, appended amendment provenance, marked the dependent graph closure stale, selectively refreshed it in one transaction, and retained genuine unresolved conditions. A later authenticated transition adopted the canonical `Symphony of Serenity` concept plus brand, delivery, and CAD 12,000 budget declarations; the six original evidence conditions are now resolved through authenticated, append-only transitions. Generated environments, original procedural audio, the Aurelian Renewal Serum prop declaration, and Noto/OFL evidence are registered. The three final edited video deliverables are registered as immutable governed VIDEO assets with preserved hashes, probe metadata, and derivation provenance. Authorized Clearance is `CLEAR TO PROCEED`, distinct independent QA is `PASS`, readiness is 100, Studio Head decision sequence 2 is `APPROVED`, and the persisted final package is `READY_FOR_DELIVERY`.

The governed production chain is complete. Remaining work is operator-bound: record/upload the demo and finish the Devpost submission; optional platform upload validation requires the client Instagram/YouTube accounts. Two generated environments, original procedural score/SFX, reproducible source, the fictional Aurelian Renewal Serum authorization, and the exact Noto Sans/OFL package are registered as governed evidence. The Devpost media and submission remain operator tasks. See [the three-minute demo runbook](docs/HACKATHON_DEMO.md).


## Public Runtime and Demo Certification

The verified Google Cloud Run service is:

```text
https://kevaro-studio-command-1016343355645.northamerica-northeast1.run.app
```

The FastAPI API and built React frontend are served from one container in project `kevaro-studio-command`, region `northamerica-northeast1`. A valid demo must show `bootstrap_source: GOVERNED_RUNTIME` and the exact Aurelian production identity; `STATIC_FALLBACK` is never presented as live state. Production-specific reads and all mutations require a signed session mapped to a persisted Crew Identity assignment.

The three-minute route is maintained in [`docs/HACKATHON_DEMO.md`](docs/HACKATHON_DEMO.md). It demonstrates Gemini/Google ADK orchestration, Parallel grounded evidence and citations, graph dependencies, evidence amendments, selective rebuild, Studio Head accountability, role-aware guidance, independent gates, and the persisted `READY_FOR_DELIVERY` final package.

## Local Setup

Python 3.12 and Node 22 match the production container:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
python -m studio_command
```

Run backend tests with `pytest -q`; run frontend checks with `npm run lint` and `npm run build` inside `frontend/`.

Local runtime credentials are optional only for features that do not call their providers. Use local environment variables for `PARALLEL_API_KEY`, `KEVARO_INTERNAL_AUTH_TOKEN`, `KEVARO_SESSION_SIGNING_SECRET`, and the configured Studio Head name. Never commit values. Cloud mode reads the Parallel, internal-auth, and session secrets through Secret Manager and receives the Google OAuth client ID through its Cloud Run secret reference. Missing cloud configuration fails startup closed. Exact IAM and environment requirements are documented in [`docs/deployment/GOOGLE_CLOUD_RUNTIME.md`](docs/deployment/GOOGLE_CLOUD_RUNTIME.md).

## Hackathon Integration Proof and Current Limitation

- **Google / Gemini:** specialist production agents run through Gemini-backed Google ADK orchestration and Google Cloud persistence/runtime boundaries.
- **Parallel:** the governed Research node exposes persisted search IDs, source citations, provenance, evidence gaps, and evidence-to-decision linkage; the Aurelian runtime currently reports `Parallel · VERIFIED` with nine grounded sources.
- **Governance:** authenticated Studio Head decisions, Crew Identity, scoped access, evidence amendments, selective graph rebuild, clearance, independent QA, and finalization gates are persisted and judge-visible.

The repository contains the final 30-second Instagram Reels, YouTube Shorts, and 4K 16:9 MP4 exports, plus recorded SHA-256 and technical metadata. Their inventory, registration evidence, completed Clearance package, completed independent-QA package, and technical report are in [`assets/aurelian/delivery/`](assets/aurelian/delivery/). The authenticated public snapshot reports readiness 100 and `READY_FOR_DELIVERY`; anonymous production access and mutation remain fail-closed.

## Final Runtime Certification — 2026-09-08

Certified against the governed Cloud Run persistence and the local finish-line worktree. The live health endpoint reports revision `kevaro-studio-command-00009-9lg` with Google Cloud, Secret Manager, Parallel credentials, protected mutation authentication, and crew-session authentication configured. The public bootstrap endpoint returns the exact Aurelian identity with `bootstrap_source: GOVERNED_RUNTIME`; the authenticated production snapshot returns `FINAL_MEDIA_APPROVED`, readiness 100, and `READY_FOR_DELIVERY`. Anonymous finalization returns 401.

The three immutable v1 VIDEO assets retain their local SHA-256 values and technical metadata. Clearance was recorded by the authorized Studio Head identity; independent QA was separately recorded by `Live Certification Operator`, distinct from the registering creator. Studio Head decision sequence 2 and final-package persistence are append-only governed records. No direct Firestore edit was used.

Exact remaining human work:

1. Record and upload the demonstration video.
2. Complete the Devpost media and submission fields.
3. Optionally validate uploads in the client Instagram and YouTube accounts when credentials are available.

## Technology

Current technology direction includes:

- Gemini
- Google Agent Development Kit
- Google Cloud
- Vertex AI
- FastAPI
- Firestore
- Cloud Storage
- Parallel Search
- React
- Vite

The hackathon runtime is intentionally kept inside the approved Google AI / Google Cloud stack plus the selected Parallel partner integration.

## Repository Structure

```text
kevaro-studio-command/
├── studio_command/        # governed backend, agents, state, persistence, API
├── frontend/              # React production command interface
├── docs/                  # canonical contract, deployment, and demo documentation
├── test_*.py              # lifecycle, governance, API, and UI-contract tests
├── README.md
└── LICENSE
```
