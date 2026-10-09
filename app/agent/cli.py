"""Interactive terminal interface for the textile production agent."""

from app.agent.tool_agent import run_agent


def chat() -> None:
    """Run an interactive conversation until the user exits."""
    conversation_history: list[dict[str, str]] = []
    print("Textile Production Chat")
    print("Type /exit or /quit to end the conversation.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if question.lower() in {"/exit", "/quit"}:
            print("Goodbye.")
            return
        if not question:
            continue

        response = run_agent(question, conversation_history.copy())
        print(f"\nAssistant: {response}\n")
        conversation_history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": response},
            ]
        )
        conversation_history = conversation_history[-40:]


if __name__ == "__main__":
    chat()
