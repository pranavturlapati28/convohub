def test_create_thread(client):
    resp = client.post("/v1/threads", json={"title": "My Project"})
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data and data["title"] == "My Project"
    return data["id"]

def test_branch_chat_and_list(client):
    # 1) thread
    t = client.post("/v1/threads", json={"title": "T1"}).json()
    thread_id = t["id"]

    # 2) branch
    b = client.post(f"/v1/threads/{thread_id}/branches", json={"name": "main"}).json()
    branch_id = b["id"]
    assert b["name"] == "main"

    # 3) send user message
    r = client.post(f"/v1/branches/{branch_id}/messages",
                    json={"role": "user", "text": "Hello branching world"})
    assert r.status_code == 200
    ids = r.json()
    assert "user_message_id" in ids and "assistant_message_id" in ids

    # 4) list messages
    msgs = client.get(f"/v1/branches/{branch_id}/messages").json()
    # Expect: seed system message (from branch creation), then user, then assistant
    roles = [m["role"] for m in msgs]
    assert roles[0] == "system"
    assert roles[1] == "user"
    assert roles[2] == "assistant"
    # Parent linkage check
    assert msgs[2]["parent_message_id"] == msgs[1]["id"]
