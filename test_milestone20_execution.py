import asyncio

from google.adk import Workflow
from google.adk.workflow import JoinNode
from google.adk.runners import InMemoryRunner


execution_log = []


def planning():
    execution_log.append("planning")
    return "planning complete"


def scheduling():
    execution_log.append("scheduling")
    return "scheduling complete"


def asset_media():
    execution_log.append("asset_media")
    return "asset media complete"


def clearance():
    execution_log.append("clearance")
    return "clearance complete"


join = JoinNode(
    name="m20_execution_join",
    description="Wait for scheduling and asset/media before clearance.",
)

workflow = Workflow(
    name="m20_execution_workflow",
    description="Milestone 20 real fan-out/fan-in execution test.",
    edges=[
        (
            "START",
            planning,
            (
                scheduling,
                asset_media,
            ),
            join,
            clearance,
        )
    ],
)


async def main():
    runner = InMemoryRunner(
        node=workflow,
        app_name="kevaro-studio-command",
    )

    user_id = "milestone20-test-user"
    session_id = "milestone20-execution-session"

    await runner.session_service.create_session(
        app_name="kevaro-studio-command",
        user_id=user_id,
        state={},
        session_id=session_id,
    )

    events = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        invocation_id="milestone20-execution",
    ):
        events.append(event)

    assert execution_log[0] == "planning"

    clearance_position = execution_log.index("clearance")

    assert execution_log.index("scheduling") < clearance_position
    assert execution_log.index("asset_media") < clearance_position

    assert set(execution_log) == {
        "planning",
        "scheduling",
        "asset_media",
        "clearance",
    }

    print("MILESTONE 20 MODERN WORKFLOW EXECUTION: PASS")
    print("Execution log:", execution_log)
    print("Events yielded:", len(events))


asyncio.run(main())
