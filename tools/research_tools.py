import os

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def web_research(query: str) -> dict:
    """Search the web using Tavily."""

    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
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

        return {
            "success": True,
            "query": query,
            "result_count": len(results),
            "results": results,
        }

    except Exception as error:
        return {
            "success": False,
            "query": query,
            "result_count": 0,
            "results": [],
            "error": str(error),
        }