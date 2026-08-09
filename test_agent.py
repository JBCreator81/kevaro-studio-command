import asyncio
import json

from vertexai import agent_engines

from studio_command.agent import root_agent


async def main():
    app = agent_engines.AdkApp(agent=root_agent)

    directive = (
        "Create and prepare a 30-second luxury wellness campaign "
        "for launch next Friday."
    )

    print("\n=== STUDIO HEAD DIRECTIVE ===")
    print(directive)

    final_brief = None
    research_packet = None
    creative_treatment = None
    production_plan = None

    async for event in app.async_stream_query(
        user_id="studio-head-demo",
        message=directive,
    ):
        author = event.get("author", "unknown")
        content = event.get("content", {})

        for part in content.get("parts", []):
            text = part.get("text")

            if not text:
                continue

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                continue

            if author == "executive_producer":
                if isinstance(parsed, dict) and "production_title" in parsed:
                    final_brief = parsed

            elif author == "research_agent":
                if isinstance(parsed, dict) and "evidence" in parsed:
                    research_packet = parsed

            elif author == "creative_development_agent":
                if isinstance(parsed, dict) and "recommended_concept" in parsed:
                    creative_treatment = parsed

            elif author == "production_manager_agent":
                if isinstance(parsed, dict) and "tasks" in parsed:
                    production_plan = parsed

    print("\n=== PRODUCTION BRIEF ===\n")
    if final_brief:
        print(json.dumps(final_brief, indent=2))
    else:
        print("No structured ProductionBrief was found.")

    print("\n=== RESEARCH PACKET ===\n")
    if research_packet:
        print(json.dumps(research_packet, indent=2))
    else:
        print("No structured ResearchPacket was found.")

    print("\n=== CREATIVE TREATMENT ===\n")
    if creative_treatment:
        print(json.dumps(creative_treatment, indent=2))
    else:
        print("No structured CreativeTreatment was found.")

    print("\n=== PRODUCTION PLAN ===\n")
    if production_plan:
        print(json.dumps(production_plan, indent=2))
    else:
        print("No structured ProductionPlan was found.")


if __name__ == "__main__":
    asyncio.run(main())
