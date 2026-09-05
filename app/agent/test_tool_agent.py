from app.agent.tool_agent import run_agent


query = "Check the current condition of loom L001 and tell me if there is any problem."

print("========================================")
print("       TEXTILE PRODUCTION AGENT")
print("========================================")

print(f"\nUser: {query}")

answer = run_agent(query)

print("\n========================================")
print("           AGENT RESPONSE")
print("========================================")
print(answer)