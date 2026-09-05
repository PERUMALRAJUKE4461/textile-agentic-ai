from tools.research_tools import web_research


result = web_research(
    "air jet loom low production causes"
)

print("========================================")
print("          WEB RESEARCH TOOL")
print("========================================")

print(f"Query: {result['query']}")
print(f"Results found: {result['result_count']}")

if result["success"]:

    for i, item in enumerate(result["results"], start=1):

        print("\n----------------------------------------")
        print(f"Result {i}")
        print(f"Title   : {item['title']}")
        print(f"URL     : {item['url']}")
        print(f"Score   : {item['score']}")
        print(f"Content : {item['content'][:500]}...")

else:

    print("\nResearch failed:")
    print(result["error"])