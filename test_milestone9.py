import asyncio
import json

from google.adk.agents import Agent
from vertexai import agent_engines

from studio_command.models import StudioHeadDecisionPackage


TEST_INSTRUCTION = """
You are the Studio Head Decision Gate for Kevaro Studio Command.

This is a focused validation of the production decision-gate logic.

The verified upstream package is:

PRODUCTION BRIEF:
Production title: Luxury Wellness Campaign
Objective: Create a 30-second luxury wellness campaign for launch next Friday.
Deadline: next Friday.

RESEARCH:
General luxury wellness research is complete.
Unresolved:
- Specific client product or service is not defined.
- Brand guidelines are missing.

CREATIVE:
Recommended concept: Quiet luxury wellness.
Unresolved:
- Exact brand identity remains unknown.

PRODUCTION PLAN:
- Finalize campaign focus.
- Confirm brand assets.
- Prepare production.

SCHEDULE:
Deadline: next Friday.
Risk: Missing client information could delay launch.

ASSETS:
Client logos and approved brand assets are not yet supplied.

CLEARANCE:
Decision: CONDITIONAL.
Final rights and brand approvals remain unresolved.

VERIFICATION QA:
Readiness score: 62.
QA decision: FAIL.
Failed check: Required client information is missing.
Unresolved:
- Brand identity.
- Approved assets.
- Distribution requirements.

OPERATING RULES

1. HUMAN AUTHORITY BOUNDARY
Never claim that the Studio Head approved or rejected anything.
You may recommend a decision only.

2. RESPECT QA AND CLEARANCE
Carry forward the QA failure, readiness score, clearance status,
material blockers, and unresolved risks accurately.

3. APPROVAL LOGIC
Allowed recommendations:
- APPROVE
- APPROVE WITH CONDITIONS
- REQUEST CHANGES
- REJECT

Do not recommend APPROVE while material blockers remain unresolved.

4. DATE INTEGRITY
The only supplied deadline is the phrase "next Friday".
Preserve that wording exactly.
Never invent or infer an absolute calendar date.
Never introduce a year or historical date.

5. FINAL WARNING
Surface the most important unresolved production risk.

Return a structured StudioHeadDecisionPackage.
"""


validation_agent = Agent(
    name="milestone9_validation_agent",
    model="gemini-2.5-flash",
    instruction=TEST_INSTRUCTION,
    output_schema=StudioHeadDecisionPackage,
)


async def main():
    app = agent_engines.AdkApp(agent=validation_agent)

    package = None

    async for event in app.async_stream_query(
        user_id="milestone9-validation",
        message="Prepare the Studio Head decision package.",
    ):
        content = event.get("content", {})

        for part in content.get("parts", []):
            text = part.get("text")
            if not text:
                continue

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict) and "recommended_decision" in parsed:
                package = parsed

    print("\n=== MILESTONE 9 DECISION PACKAGE ===\n")
    print(
        json.dumps(package, indent=2)
        if package
        else "No structured StudioHeadDecisionPackage was found."
    )

    if not package:
        raise SystemExit("FAIL: No structured decision package returned.")

    serialized = json.dumps(package)

    if "next Friday" not in serialized:
        raise SystemExit(
            "FAIL: Relative deadline 'next Friday' was not preserved."
        )

    for year in ("2024", "2025", "2026", "2027"):
        if year in serialized:
            raise SystemExit(
                f"FAIL: Unsupported absolute year {year} was introduced."
            )

    if package.get("recommended_decision") == "APPROVE":
        raise SystemExit(
            "FAIL: Unconditional approval was recommended despite material blockers."
        )

    print("\nMILESTONE 9 REDUCED-CALL VALIDATION: PASS")


if __name__ == "__main__":
    asyncio.run(main())
