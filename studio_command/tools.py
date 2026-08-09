import os
from parallel import Parallel


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
        }

    client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])

    response = client.search(
        objective=objective,
        search_queries=search_queries,
    )

    return {
        "status": "success",
        "search_id": response.search_id,
        "session_id": response.session_id,
        "results": [
            {
                "title": result.title,
                "url": result.url,
                "excerpts": result.excerpts[:3] if result.excerpts else [],
            }
            for result in response.results
        ],
    }
