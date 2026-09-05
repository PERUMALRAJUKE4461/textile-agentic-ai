from app.agent.llm import ask_llm


response = ask_llm(
    "You are a textile manufacturing assistant. "
    "Explain in two sentences why monitoring machine vibration is important."
)

print(response)
