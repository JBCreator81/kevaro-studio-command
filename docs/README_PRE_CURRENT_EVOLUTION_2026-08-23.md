# Kevaro Studio Command

**One Studio Head. An autonomous production crew.**

Kevaro Studio Command is an AI-native production command system that turns a creative directive into researched, coordinated, created, independently verified, production-ready work using Gemini and Google Cloud.

## Competition Build

Kevaro Studio Command is a newly created project for the **2026 Agentic Cinema: The Blockbuster Hackathon**.

This repository is a clean-room build. It does **not** modify, fork, copy, import, or reuse source code, schemas, components, prompts, tests, styling, or implementation from Kevaro OS RC v1.0. Only high-level lessons and general architectural principles are being carried forward.

## Product Thesis

Creative teams already have many tools for writing, editing, scheduling, review, assets, and delivery. Kevaro Studio Command is designed to become the **production command layer above that work**.

Its purpose is not merely to store production information. Its purpose is to move productions forward.

> **Not just a single source of truth. A single source of action.**

A Studio Head issues a production directive. A governed network of specialized agents then researches, plans, creates, coordinates, executes, verifies, corrects, and prepares the final production package while escalating only decisions that genuinely require human judgment.

## Core Operating Model

**One human session → many coordinated agents → automatic handoffs → human decision gates only when necessary**

The Studio Head remains in one authenticated session. Specialist agents operate internally and never require the user to switch identities or logins.

Planned specialist roles include:

- Executive Producer Agent
- Research Agent
- Creative Director Agent
- Production Manager Agent
- Production Scheduling Agent
- Media & Assets Agent
- Clearance & Compliance Agent
- Production QA Agent

Each agent has a defined responsibility, permissions, tool access, measurable completion criteria, explicit handoff rules, and auditable actions.

## Governing Principles

- Evidence Before Execution
- Graph, not chain
- Human approval only where it adds value
- Execution agents cannot verify their own work
- Real tool use, not simulated autonomy
- Clear production state and measurable completion
- Auditable actions and decisions
- Minimal user friction
- Premium cinematic user experience
- Authentic film, television, advertising, and creative-production terminology
- Learn continuously, change deliberately
- New features must pass a value gate before entering the MVP

## Competition Technology Direction

The competition build is designed around:

- Gemini
- Google Agent Development Kit (ADK)
- Google Cloud / Gemini Enterprise Agent Platform
- Cloud Run
- Firestore
- Cloud Storage
- Parallel Search as the runtime evidence and grounding layer

The submitted runtime is intended to remain within approved Google Cloud AI tooling and the selected partner technology.

## Signature MVP Experiences

### 1. Studio Command Center
A premium Studio Head control surface focused on production readiness, current activity, blockers, and decisions that actually require attention.

### 2. Live Agent Production Graph
A visual, stateful production graph that shows agents planning, acting, using tools, handing work off, correcting failures, and reaching completion.

### 3. Parallel Evidence Room
A first-class evidence experience showing research questions, sources, findings, relevance, uncertainty, and the downstream production decisions influenced by that evidence.

### 4. Visual Development Room
Creative direction, mood boards, visual references, storyboard concepts, camera language, lighting, palette, and approval gates presented in a cinematic workflow.

### 5. Independent Multimodal QA
A separate QA function that evaluates work against predefined acceptance criteria and can route failed work back for correction and re-verification. Where useful, QA should evaluate text, images, audio, and video.

### 6. Final Production Package
A completed production should resolve into a professional package containing the approved creative, production plan, evidence, assets, QA results, governance record, and delivery information.

## Production Intelligence Foundation

The data architecture should support future capabilities from the beginning, including:

- Production Memory / Production Bible
- Change Impact Engine
- Studio Preference Memory
- Workflow Adaptation
- Agent Performance Memory
- Pattern and bottleneck detection
- Learning from corrections
- Versioned templates and operating rules
- Controlled self-improvement proposals
- Cross-production intelligence within strict privacy boundaries

The system may learn from production history, but material governance, safety, permissions, and verification rules must never change silently.

## Human Decision Model

Studio Command classifies decisions into three categories:

- **AUTO** — reversible, low-risk actions the system may execute autonomously
- **APPROVAL REQUIRED** — material creative, delivery, budget, public-claim, or release decisions for the Studio Head
- **EXCEPTION** — blocked or unsafe states that require escalation

The goal is to protect human attention as a limited production resource.

## Real Tool Action and Auditability

Important operations should occur through structured tools and functions rather than unconstrained prose. Examples include:

- research calls
- production state updates
- approval requests
- scheduling actions
- evidence records
- QA results
- retries and correction routing
- final completion

Each meaningful action should emit an auditable event describing who or what acted, which tool was used, what production node was affected, the result, and verification status.

## Measurable Outcome

The demo should make the system's operational value visible through metrics such as:

- autonomous production tasks completed
- evidence sources consulted
- agent handoffs
- human approvals required
- QA defects detected
- defects corrected and re-verified
- role switches avoided
- manual assignments avoided
- production readiness

## Example Production Directive

> Create and prepare a 30-second luxury wellness campaign for launch next Friday. Produce the creative direction, research-backed concept, script, storyboard/shot plan, production schedule, supporting assets, QA review, and final production-ready package.

The intended experience is that one directive starts a governed production graph and the Studio Head intervenes only at meaningful gates.

## Visual Direction

Kevaro Studio Command should feel like premium software built for movie, television, advertising, and media creators rather than a generic admin dashboard.

The interface direction is cinematic, restrained, polished, highly visual, and production-native, with purposeful motion, large production surfaces, evidence cards, visually compelling agent activity, and a memorable **Ready for Launch / Ready for Delivery** completion experience.

## Development Status

Active competition build.

Milestones 1-15 are complete and validated on the main branch:

- Executive Producer / Orchestrator
- Research
- Creative Development
- Production Manager
- Scheduling
- Asset & Media
- Clearance & Compliance
- Independent Verification & QA
- Studio Head Decision Gate
- Human Studio Head Decision Recording
- Production Decision Routing
- Append-Only Decision History
- Corrective Work Cycle
- Independent Re-Review Gate
- Fresh Studio Head Reapproval and New Decision Sequence

The build has now reached the architecture-integration phase.

## Canonical Production Architecture

Kevaro Studio Command is governed by six cooperating foundations.

### 1. Agent Production Graph

Specialist agents perform production work through a dependency-aware graph.

The finished runtime must preserve the principle:

**Build a graph, not a chain.**

Work that can safely run in parallel should branch into parallel production workstreams and reconverge only when dependencies or approval gates require it.

The current sequential orchestration used during early milestone validation is a foundation, not the final operating model.

### 2. Governance & State Engine

Every consequential production transition must be explicit, deterministic, and auditable.

The Studio Head retains final human authority.

Supported human decisions are:

- APPROVE
- APPROVE WITH CONDITIONS
- REQUEST CHANGES
- REJECT

A request for changes must route to corrective work.

Corrective work must pass independent re-verification before returning to the Studio Head.

A successful re-verification may never bypass a fresh Studio Head decision.

Human decisions are append-only and must never silently overwrite prior history.

### 3. Production Memory

Kevaro must preserve the current production truth across the full production life cycle.

Production Memory should retain relevant versions and state for:

- production briefs
- evidence and research
- creative direction
- production plans
- schedules
- media and assets
- clearance records
- QA results
- human decisions
- corrective work
- active conditions
- approved versions
- known-good recovery points
- production state and history

Production Memory is intended to become the persistent Production Bible for each production.

### 4. Change Impact Engine

Before a meaningful change propagates, Kevaro must determine what that change affects.

The system should identify:

- work that remains valid
- work that becomes stale
- work that must reopen
- approvals that become invalid
- evidence that must be refreshed
- clearance that must be rechecked
- QA that must be rerun
- schedule or delivery consequences

The governing rule is:

**Do not restart unaffected work.**

Only genuinely affected production nodes should be reopened or invalidated.

### 5. Command Safety & Conflict Intelligence

Human authority remains final, but consequential Studio Head commands must not execute blindly.

Before a material command executes, Kevaro should evaluate it against:

- active production state
- existing approvals
- dependencies
- active work
- evidence
- clearance
- QA status
- schedule
- delivery commitments
- conflicting commands
- affected productions, scenes, assets, or workstreams

Kevaro must detect stale, conflicting, ambiguous, high-impact, or potentially destructive instructions before execution.

### 6. Audit & Recovery Layer

Material actions, decisions, overrides, tool use, state changes, retries, corrections, and approvals should emit an auditable record.

Where a high-impact action is reversible, Kevaro should preserve a known-good prior state so production can recover without unnecessary rebuilding.

## Studio Head Authority Doctrine

Kevaro follows this operating principle:

> **Kevaro advises, protects, and explains. The Studio Head decides.**

The Studio Head retains final approval authority after being shown the production consequences of a material decision.

Kevaro must never silently replace human judgment.

Kevaro must also never blindly execute a consequential command without explaining the likely production impact.

Hard legal, safety, permission, platform, or system restrictions remain hard gates.

## Studio Head Impact Brief

Before a consequential Studio Head command or override executes, Kevaro should present a concise Studio Head Impact Brief using plain production language rather than technical system language.

The Impact Brief should explain:

- what changed
- what production work is affected
- what remains valid
- what becomes stale or must be redone
- schedule impact
- delivery impact
- budget or resource impact when known
- clearance or rights impact
- continuity impact
- QA impact
- affected downstream work
- recommended production path
- consequences of proceeding anyway

The Studio Head should receive meaningful options such as:

- Approve Recommended Path
- Approve With Conditions
- Proceed Anyway
- Send Back for Changes
- Cancel Command

When an informed override is allowed, Kevaro should record what was warned about, what recommendation was overridden, who approved the override, and which production risks were knowingly accepted.

## Command Safeguards

The unified runtime should include:

### Stale Decision Protection

If evidence, QA, clearance, or production state changes after a Studio Head decision package was prepared, the package becomes stale and must refresh before approval can execute.

### Scope Protection

Ambiguous commands such as "change everything", "delete the old version", or "use this everywhere" must resolve their exact production scope before destructive execution.

### Conflict Detection

Contradictory instructions, conflicts with approved direction, active work, dependencies, clearance, schedule, or other commands must be surfaced before execution.

### Impact Classification

Low-impact reversible actions may proceed normally.

Consequential actions require an Impact Brief.

High-impact or irreversible actions require deliberate human confirmation.

### Selective Invalidation

A change to one part of production must not automatically invalidate the entire production.

Only directly or transitively affected nodes should reopen.

### Known-Good Recovery

Important reversible changes should preserve the previous valid production state for safe rollback.

## Canonical Production Flow

The intended end-to-end production flow is:

Studio Head Directive
→ Executive Producer
→ Evidence & Research
→ Creative Development
→ Production Planning
→ Stateful Production Graph
→ Scheduling / Assets / Clearance / parallel production work
→ Independent QA
→ Studio Head Decision Package
→ Human Studio Head Decision
→ Deterministic State Transition
→ Append-Only Decision History
→ Approved Execution OR Corrective Cycle
→ Change Impact Analysis where required
→ Selective Rework
→ Independent Re-Verification
→ Fresh Studio Head Reapproval
→ Final Production Execution
→ Final Production Package
→ Ready for Delivery

## Remaining Build Roadmap

### Milestone 16 — Unified Governed Production Runtime

Connect:

- Agent Production Graph
- Governance & State Engine
- Production Memory
- Change Impact Engine
- Command Safety & Conflict Intelligence
- Audit & Recovery

A production should be able to move through human decision, preserve state and history, respond intelligently to changes, reopen only affected work, and resume from the correct state.

### Milestone 17 — Approved Production Execution

Real downstream production actions may execute only from properly authorized workflow states.

Conditional approvals must carry active conditions into execution.

Rejected and change-requested paths must remain blocked.

### Milestone 18 — Persistent Production Memory & Recovery

Persist production state, artifacts, versions, history, known-good snapshots, and recovery data using the competition runtime infrastructure.

### Milestone 19 — True Live Production Graph & Change Propagation

Evolve the validated sequential foundation into the intended stateful production graph with:

- parallel workstreams
- dependency-aware routing
- reconvergence
- selective invalidation
- live node state
- change propagation
- recovery-aware resumption

### Milestone 20 — Studio Command Center & Signature Experiences

Deliver the premium production-native interface including:

- Studio Command Center
- Live Agent Production Graph
- Parallel Evidence Room
- Visual Development
- Independent Multimodal QA
- Studio Head Impact Brief
- production memory and change-impact visibility

### Milestone 21 — Final Production Package & Delivery Runtime

Resolve approved production work into a professional final package containing:

- approved creative
- production plan
- evidence
- media and assets
- QA results
- governance history
- decision history
- clearance records
- delivery information
- production readiness

### Milestone 22 — Competition Hardening & Deployment

Complete:

- Google Cloud deployment
- failure and retry handling
- runtime proof
- judge-visible tool evidence
- measurable production outcomes
- demo production
- screenshots
- submission video
- competition documentation
- final Devpost readiness

## Winning Standard

Kevaro Studio Command is being built to compete for first place.

The product should also demonstrate enough operational value, technical depth, production realism, and product maturity that a studio, agency, technology partner, or investor could reasonably want to continue the conversation after seeing the demo.

The governing product standard is:

> **Build to win the competition. Build it well enough that winning is not the only valuable outcome.**

The final demo should prove that Kevaro can:

- execute a governed production from one Studio Head directive
- use real evidence and tools
- coordinate specialist agents
- preserve human authority
- detect production conflicts
- explain consequences in plain studio language
- protect unaffected work during revisions
- route only impacted work for correction
- independently re-verify corrections
- preserve decision and production history
- resume from the correct production state
- surface measurable operational value
- finish with a memorable Ready for Delivery experience

## License

Licensed under the Apache License 2.0. See `LICENSE`.
