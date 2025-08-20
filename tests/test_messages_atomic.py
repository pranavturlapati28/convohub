# tests/test_messages_atomic.py
from uuid import uuid4
from app.routers import messages as messages_router

def test_chat_turn_atomic_on_failure(client, monkeypatch):
    # thread + branch
    t = client.post("/v1/threads", json={"title": "Atomic"}).json()
    b = client.post(f"/v1/threads/{t['id']}/branches", json={"name": "main"}).json()
    branch_id = b["id"]

    # Break assistant_reply to raise (after user message would be added if not atomic)
    def boom(_history):
        raise RuntimeError("kaboom")
    monkeypatch.setattr(messages_router, "assistant_reply", boom)

    r = client.post(f"/v1/branches/{branch_id}/messages", json={"role": "user", "text": "Hello"})
    assert r.status_code == 500  # our handler returns 500 on failure

    # No messages should have been written beyond the seed system message
    msgs = client.get(f"/v1/branches/{branch_id}/messages").json()
    roles = [m["role"] for m in msgs]
    assert roles == ["system"]  # no user/assistant messages persisted
