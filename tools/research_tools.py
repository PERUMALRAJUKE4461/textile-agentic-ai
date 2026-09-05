import logging

from tavily import TavilyClient

from app.config import load_settings


LOGGER = logging.getLogger(__name__)
settings = load_settings()

tavily_client = TavilyClient(
    api_key=settings.tavily_api_key or "missing-api-key"
)


def web_research(query: str) -> dict[str, object]:
    """Search the web using Tavily."""

    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "error_code": "invalid_research_query",
            "query": query,
            "result_count": 0,
            "results": [],
            "error": "Research query must be a non-empty string.",
        }

    current_settings = load_settings()
    if not current_settings.tavily_api_key:
        LOGGER.error("Tavily API key is not configured")
        return {
            "success": False,
            "error_code": "missing_tavily_api_key",
            "query": query,
            "result_count": 0,
            "results": [],
            "error": "Tavily API key is not configured.",
        }

    try:
        response = tavily_client.search(
            query=query.strip(),
            search_depth="advanced",
            max_results=current_settings.research_max_results,
        )

        results = []

        for item in response.get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                }
            )

        if not results:
            LOGGER.warning("Tavily returned no results for the requested query")
            return {
                "success": False,
                "error_code": "empty_research_results",
                "query": query,
                "result_count": 0,
                "results": [],
                "error": "No web research results were returned.",
            }

        LOGGER.info("Web research completed with %d results", len(results))
        return {
            "success": True,
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    except TimeoutError as error:
        LOGGER.error("Tavily request timed out: %s", error)
        return {
            "success": False,
            "error_code": "research_timeout",
            "query": query,
            "result_count": 0,
            "results": [],
            "error": "Tavily research request timed out.",
        }
    except Exception as error:
        if "timeout" in type(error).__name__.lower() or "timeout" in str(error).lower():
            LOGGER.error("Tavily request timed out")
            return {
                "success": False,
                "error_code": "research_timeout",
                "query": query,
                "result_count": 0,
                "results": [],
                "error": "Tavily research request timed out.",
            }
        LOGGER.error("Tavily request failed: %s", error)
        return {
            "success": False,
            "error_code": "research_api_error",
            "query": query,
            "result_count": 0,
            "results": [],
            "error": "Tavily research request failed.",
        }