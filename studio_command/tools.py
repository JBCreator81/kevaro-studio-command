from datetime import datetime, timezone
from urllib.parse import urlparse
from parallel import Parallel
from google.adk.tools import ToolContext
from studio_command.runtime_config import RuntimeConfig, load_runtime_config


def _model_dict(value) -> dict:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else {}


def _record_search_result(tool_context: ToolContext | None, output: dict) -> None:
    if tool_context is None:
        return
    tool_context.state["parallel_search_result"] = output
    function_call_id = getattr(tool_context, "function_call_id", None)
    if not function_call_id:
        existing = sum(
            key.startswith("parallel_search_call:")
            for key in tool_context.state
        )
        function_call_id = f"direct-{existing + 1}"
    tool_context.state[f"parallel_search_call:{function_call_id}"] = {
        "function_call_id": function_call_id,
        "research_run_id": getattr(tool_context, "invocation_id", None),
        "result": output,
    }


def search_web(
    objective: str, search_queries: list[str], *,
    runtime_config: RuntimeConfig | None = None,
    tool_context: ToolContext | None = None,
) -> dict:
    """
    Search the live web with Parallel and return compact,
    source-grounded evidence for the Research Agent.
    """

    config = runtime_config or load_runtime_config()
    if not config.parallel_api_key:
        output = {
            "status": "error",
            "message": "PARALLEL_API_KEY is not configured.",
            "results": [],
            "provenance": {
                "provider": "Parallel", "verification_status": "UNAVAILABLE",
                "objective": objective, "search_queries": search_queries,
                "unavailable_reason": "PARALLEL_API_KEY is not configured.",
                "research_node": "Research",
            },
        }
        _record_search_result(tool_context, output)
        return output

    invoked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    client = Parallel(api_key=config.parallel_api_key)

    response = client.search(
        objective=objective,
        search_queries=search_queries,
    )

    results = [
        {
            "title": result.title,
            "url": result.url,
            "source": urlparse(result.url).hostname,
            "citation_id": f"parallel:{response.search_id}:{index}",
            "excerpts": result.excerpts[:3] if result.excerpts else [],
            "publish_date": result.publish_date,
        }
        for index, result in enumerate(response.results, start=1)
    ]
    output = {
        "status": "success", "search_id": response.search_id,
        "session_id": response.session_id, "results": results,
        "provenance": {
            "provider": "Parallel", "verification_status": "VERIFIED",
            "objective": objective, "search_queries": search_queries,
            "invoked_at": invoked_at, "search_id": response.search_id,
            "session_id": response.session_id,
            "invocation_marker": f"parallel-search:{response.search_id}",
            "result_count": len(results),
            "usage": [_model_dict(x) for x in (response.usage or [])],
            "warnings": [_model_dict(x) for x in (response.warnings or [])],
            "research_node": "Research",
        },
    }
    _record_search_result(tool_context, output)
    return output
