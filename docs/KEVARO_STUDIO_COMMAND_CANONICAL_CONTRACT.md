# Kevaro Studio Command — Canonical Product & Build Contract

## Status
This document is the authoritative requirements and product-direction contract for Kevaro Studio Command. It is additive to the implementation in this repository. New work must not silently weaken, replace, or drift from requirements already locked here.

GitHub remains the source of truth for the build. Google Cloud provides the runtime environment. Firestore and Cloud Storage provide governed production-state and artifact persistence.

## Product Thesis
**One Studio Head. A governed production crew of humans and agents.**

Kevaro Studio Command is not merely an AI assistant or project dashboard. It is a governed production-command operating layer that coordinates research, creative development, planning, scheduling, media/assets, clearance, verification, human decisions, change impact, and delivery.

**Evidence → Decision → Execution**

## Governing Principles
- Evidence Before Execution
- Build a graph, not a chain
- Human approval only where it adds value
- Execution agents cannot verify their own work
- Real tool use, not simulated autonomy
- Explicit production state transitions
- Auditability and provenance
- Production memory and known-good recovery
- Preserve unaffected work during change
- Learn continuously, change deliberately
- Premium cinematic UX
- Authentic production terminology
- Near-zero-training usability
- Read what you need. Edit what you own. Approve only what your role permits. Studio Head governs everything.

## Core Governed Agent Architecture
- Executive Producer / Orchestrator
- Research Agent
- Creative Development Agent
- Production Manager Agent
- Scheduling Agent
- Asset & Media Agent
- Clearance & Compliance Agent
- Independent Verification / QA Agent
- Studio Head Decision Gate

## Human Authority
Supported decisions:
- APPROVE
- APPROVE WITH CONDITIONS
- REQUEST CHANGES
- REJECT

Studio Head attention is a limited production resource. Routine specialist technical choices should not be escalated unless they materially affect creative intent, scope, budget, schedule, quality, legal exposure, safety, or explicit delivery requirements.

## Production Memory
Kevaro preserves production truth across:
- briefs
- evidence and research
- creative direction
- plans
- schedules
- assets
- clearance
- QA
- decisions
- corrective work
- approved artifacts
- known-good states
- final delivery
- production history

## Reality Shift / Change Impact
When production reality changes, Kevaro determines:
- what remains valid
- what becomes stale
- what must reopen
- which approvals become invalid
- which evidence must refresh
- which clearance must rerun
- which QA must rerun
- schedule and delivery consequences

**Do not restart unaffected work.**

## Full Node Intelligence
Every production-graph node must expose the real governed artifact behind it, not only status.

Production Brief:
objective, deliverables, audience, constraints, budget, deadline, assumptions, approvals.

Research:
Parallel sources, findings, citations, provenance, relevance, uncertainty, unresolved questions, evidence gaps, downstream decisions influenced.

Creative Development:
treatment, concept, tone, messaging, visual direction, references, risks, approval state.

Production Planning:
tasks, owners, dependencies, requirements, budget implications, blockers, completion criteria.

Scheduling:
scheduled tasks, dependencies, parallel groups, critical path, buffers, approval windows, deadline threats.

Asset & Media:
required assets, sourcing, rights/licensing, formats, missing items, media risks, delivery requirements.

Clearance & Compliance:
clearance state, checks, cleared items, blocked items, rights requirements, claim restrictions, legal risks, next actions.

Verification QA:
findings, checks, failures, unresolved items, cross-artifact conflicts, technical validation, evidence validation, readiness score, next QA actions.

Studio Head Decision:
recommendation, rationale, human decisions, conditions, blockers, history, authorization state.

Final Package:
approved deliverables, evidence, governance record, QA, readiness, delivery status, final notes.

## Parallel Evidence Visibility
Parallel must be visibly integrated throughout the product:
- research objective
- runtime participation
- sources/citations
- provenance
- evidence freshness and relevance
- decision impact
- distinction between sourced evidence and agent reasoning

The Parallel Evidence Room is a first-class experience.

## Production Accountability / Crew Identity
Every important artifact and node should show:
- human owner
- AI agent responsible
- contributors
- reviewer / verifier
- approved by
- last changed by
- timestamp
- status
- action / decision history

Accountability supports collaboration and traceability, not opaque surveillance.

## Production Access Control & Work Ownership
**Read what you need. Edit what you own. Approve only what your role permits. Studio Head governs everything.**

Studio Head:
full production-wide visibility and governance.

Assigned Owner:
edit rights to owned tasks and artifacts.

Contributor:
edit only assigned sections or deliverables.

Reviewer / Verifier:
read, review, comment, verify, approve or return where permitted, without silently rewriting creator work.

Downstream Worker:
read approved dependencies required for their work, without modifying upstream artifacts.

Unassigned Crew:
limited/no edit access.

Changes to someone else’s completed or approved work must go through governed change control / Reality Shift.

## Role-Aware Guidance & Next Best Action
Kevaro should tell each user:
- their role
- assigned work
- what is waiting on them
- what they can edit
- what they can only view
- what context to review
- missing evidence/files
- next action
- what happens after completion
- when to escalate

Guidance layers:
- Contextual Guidance
- Next Best Action
- Guided Workflows
- Guided / Standard / Expert depth

## Near-Zero-Training Usability
Training time is production cost.

A newly invited crew member, contractor, or freelancer should be able to enter a governed production and begin the correct assigned work within minutes.

Long-term product metric:
**Time-to-Productive-Work**

## Production Accountability Chain
**Crew Identity → Work Ownership → Scoped Access → Role-Aware Guidance → Node Intelligence → Evidence → Verification → Human Approval → Audit Trail → Final Delivery**

Reality Shift overlays this chain by determining which work remains trustworthy after change.

## Premium Product Experience
Kevaro must feel like premium cinematic production-command software.

Required:
- cinematic opening experience
- premium dark command-centre visual language
- large production surfaces
- purposeful motion
- production-native terminology
- Live Production Graph
- Parallel Evidence Room
- Visual Development
- Independent QA
- Studio Head approval gates
- polished Final Production Package
- judge-facing clarity within the first 30–60 seconds

## Auditability
Meaningful actions should record:
- actor
- role
- node/artifact
- tool/action
- evidence used
- result
- verification state
- timestamp
- human decision where required

## Canonical Production Identity
Every persisted production must resolve consistently across:
- pending review bundle
- Studio Head decision package
- governed runtime state
- approved artifacts
- final package
- Firestore
- production-specific API routes
- UI routes

Anonymous or inconsistent production identity is not acceptable in the finished system.

## Current Remaining Priorities
1. Repair canonical production identity persistence.
2. Complete Full Node Intelligence with real persisted artifacts.
3. Implement Crew Identity / Accountability.
4. Implement backend-enforced Work Ownership and Access Control.
5. Implement Role-Aware Guidance and Next Best Action.
6. Make Parallel evidence fully visible.
7. Complete premium cinematic opening and UI polish.
8. Run a fresh end-to-end current-schema live production.
9. Simplify demo startup and runtime reliability.
10. Deploy to final public Google Cloud URL.
11. Complete README, architecture proof, screenshots, demo video, compliance evidence, and Devpost submission.

## Change Rule
Future core requirements must be added here and implemented without weakening existing governed behaviour.

**Learn continuously. Change deliberately. Preserve the contract.**
