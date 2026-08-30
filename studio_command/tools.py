import os
from datetime import datetime, timezone
from urllib.parse import urlparse
from parallel import Parallel


def _model_dict(value) -> dict:
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else {}


def search_web(objective: str, search_queries: list[str]) -> dict:
    """
    Search the live web with Parallel and return compact,
    source-grounded evidence for the Research Agent.
    """

    if not os.getenv("PARALLEL_API_KEY"):
        return {
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

    invoked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])

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
    return {
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
