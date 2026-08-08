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

    async for event in app.async_stream_query(
        user_id="studio-head-demo",
        message=directive,
    ):
        author = event.get("author", "unknown")

        if author == "executive_producer":
            content = event.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")

                if not text:
                    continue

                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict) and "production_title" in parsed:
                        final_brief = parsed
                except json.JSONDecodeError:
                    pass

    print("\n=== PRODUCTION BRIEF ===\n")

    if final_brief:
        print(json.dumps(final_brief, indent=2))
    else:
        print("No structured ProductionBrief was found.")


if __name__ == "__main__":
    asyncio.run(main())
