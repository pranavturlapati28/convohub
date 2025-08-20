# For day-1, keep a deterministic echo. We’ll swap to LangGraph next.
def assistant_reply(history: list[dict]) -> str:
    last_user = next((m["content"] for m in reversed(history) if m["role"]=="user"), "")
    return f"(echo) You said: {last_user[:200]}"
