def _make_branch(client, name="main"):
    t = client.post("/v1/threads", json={"title": "T"}).json()
    thread_id = t["id"]
    b = client.post(f"/v1/threads/{thread_id}/branches", json={"name": name}).json()
    return thread_id, b["id"]

def _say(client, branch_id, text):
    r = client.post(f"/v1/branches/{branch_id}/messages", json={"role": "user", "text": text})
    assert r.status_code == 200
    return r.json()

def test_placeholder_merge_commit(client):
    # create two branches in same thread
    thread_id, main_id = _make_branch(client, "main")
    _, idea_id = _make_branch(client, "idea-A")  # (separate branch in a separate thread would fail merge)
    # NOTE: merges expect same thread; use two branches under same thread instead:
    # Let's do it correctly:
    t = client.post("/v1/threads", json={"title": "Thread"}).json()
    thread_id = t["id"]
    main = client.post(f"/v1/threads/{thread_id}/branches", json={"name": "main"}).json()
    idea = client.post(f"/v1/threads/{thread_id}/branches", json={"name": "idea-A"}).json()
    main_id, idea_id = main["id"], idea["id"]

    # diverge both
    _say(client, main_id, "Main work 1")
    _say(client, idea_id, "Idea work 1")

    # merge placeholder
    m = client.post("/v1/merge", json={
        "thread_id": thread_id,
        "source_branch_id": idea_id,
        "target_branch_id": main_id,
        "strategy": "hybrid"
    })
    assert m.status_code == 200
    payload = m.json()
    assert "merge_id" in payload and "merged_into_message_id" in payload

    # target branch should have a new assistant "merge commit" message
    msgs = client.get(f"/v1/branches/{main_id}/messages").json()
    texts = [m["content"]["text"] for m in msgs if m["role"] == "assistant"]
    assert any("merged" in t for t in texts)
