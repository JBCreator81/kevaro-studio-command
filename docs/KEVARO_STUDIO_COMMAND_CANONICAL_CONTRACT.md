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

## Final Locked Completion Scope
The following requirements are additive to all earlier canonical requirements and define the final completion scope before submission. They must not be interpreted to weaken, replace, or rewrite earlier governance.

### Production Asset Ingress & External Tool Handoff
- Users must be able to upload production work into the relevant production, node, or task.
- Supported production assets should include video, audio, images, scripts, documents, storyboards, graphics, and related media.
- Every asset must preserve production identity, node/task association, human owner, AI agent where applicable, version, timestamp, status, review state, and provenance.
- Earlier versions must never be silently replaced. Version history must be preserved.
- Uploaded work must flow into the appropriate review, QA, clearance, approval, and final-delivery lifecycle.
- Kevaro Studio Command is the production command and governance layer, not a replacement for professional editing applications such as Premiere Pro, DaVinci Resolve, After Effects, Photoshop, Canva, Frame.io, or similar specialist tools.
- External tools may receive governed assignments and return finished or revised assets into Kevaro.
- External handoff must preserve the brief, requirements, evidence, owner, due date, approvals, and expected deliverable.
- Returned work must reconcile against the correct production and version before QA or approval.
- Future connectors may support Google Drive, Cloud Storage, Frame.io, Adobe workflows, Dropbox, DAM systems, review platforms, calendars, and similar production services.
- Lightweight in-Kevaro review is in scope: preview/playback, version comparison, comments, annotations or timecoded feedback where practical, and approve/request changes.
- Full NLE/editor functionality is out of scope.

Product principle:
**Create where the work is best created. Govern it where the production is best governed.**

Canonical flow:
**Assignment → Guidance → Creation in Kevaro or External Tool → Upload/Handoff → Version Control → Evidence → QA → Review → Human Approval → Final Delivery**

### Competition Runtime Proof / Certification
- Parallel must be visibly proven at runtime, with grounding metadata and source citations exposed in the judge-facing experience.
- Gemini/Google ADK runtime must be visibly verifiable as the orchestration and intelligence layer.
- Production Asset Ingress must work in the live submitted product, not only exist in documentation.
- Deployed secrets, including the Parallel API key, must use Google Secret Manager or equivalent approved Google Cloud secret handling.
- The final hosted judge path must be reliable and repeatable.
- Final certification must use the exact deployed, current-schema product.

### Final Locked Remaining Product Work
- canonical production identity
- full live Node Intelligence, including pre-approval/pending-review usability
- Crew Identity and accountability
- work ownership and backend-enforced scoped access
- Role-Aware Guidance / Next Best Action
- Parallel Evidence visibility and citations
- Production Asset Ingress
- External Tool Handoff
- asset versioning and lightweight review
- Google Secret Manager integration
- premium cinematic UI polish, including a strong intro and production graph/nodes visibly coming to life
- fresh end-to-end governed production certification
- public Google Cloud deployment
- README/run-instruction finalization
- public repository and licence verification
- Parallel partner-track selection
- completed Devpost form
- 3-minute demo video showing the real working product
- final screenshots, runtime evidence, and submission packaging

### Scope Freeze
After this lock, no new voluntary product features may be added before submission.

Only the following may enter scope:
- bug fixes
- competition-compliance fixes
- reliability or security fixes
- implementation work required to make an already-locked requirement function correctly

### Codex Completion Rule
Codex is the primary implementation engine for the remaining repository-level engineering work. Work must proceed in bounded milestones.

For every milestone, Codex must:
- inspect the canonical contract first
- preserve existing architecture and governance unless the locked requirement genuinely requires a change
- avoid unrelated refactors
- report files changed
- report assumptions
- run appropriate tests and build validation
- report exact validation results
- report unresolved risks or blockers
- stop for review before starting the next milestone
- never silently broaden scope

ChatGPT/Prime remains the orchestration and review layer for architecture, competition compliance, prioritization, judge strategy, and milestone acceptance.

### Completion Sequence
**Product completion → end-to-end certification → public deployment → evidence/package validation → 3-minute demo → Devpost submission**

## Change Rule
Future core requirements must be added here and implemented without weakening existing governed behaviour.

**Learn continuously. Change deliberately. Preserve the contract.**
