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

Milestones 1-9 are complete and validated on the main branch:

- Executive Producer / Orchestrator
- Research
- Creative Development
- Production Manager
- Scheduling
- Asset & Media
- Clearance & Compliance
- Independent Verification & QA
- Studio Head Decision Gate

Current focus: human approval actions, corrective routing, production state,
application runtime, Studio Command UI, and final deployment hardening.

## License

Licensed under the Apache License 2.0. See `LICENSE`.
