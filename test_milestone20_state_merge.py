from types import SimpleNamespace

from studio_command.agent import _merge_parallel_planning_state


ctx = SimpleNamespace(state={})

payload = {
    "scheduling_agent": {
        "production_schedule": {
            "scheduled_tasks": ["task-a"]
        }
    },
    "asset_media_agent": {
        "asset_media_plan": {
            "asset_requirements": ["asset-a"]
        }
    },
}

result = _merge_parallel_planning_state(
    ctx,
    payload,
)

assert ctx.state["production_schedule"] == {
    "scheduled_tasks": ["task-a"]
}

assert ctx.state["asset_media_plan"] == {
    "asset_requirements": ["asset-a"]
}

assert result["production_schedule"] == ctx.state["production_schedule"]
assert result["asset_media_plan"] == ctx.state["asset_media_plan"]

print("MILESTONE 20 DIRECT STATE MERGE REGRESSION: PASS")
