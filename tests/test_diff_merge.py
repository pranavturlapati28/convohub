# tests/test_diff_merge.py
def _mk_thread_branch(client, title, name):
    t = client.post("/v1/threads", json={"title": title}).json()
    b = client.post(f"/v1/threads/{t['id']}/branches", json={"name": name}).json()
    return t["id"], b["id"]

def _say(client, branch_id, text):
    r = client.post(f"/v1/branches/{branch_id}/messages", json={"role": "user", "text": text})
    assert r.status_code == 200
    return r.json()

def test_diff_and_merge_happy_path(client):
    thread_id, main_id = _mk_thread_branch(client, "MergeX", "main")
    # fork another branch from main tip
    ids = _say(client, main_id, "main-ctx")
    tip = ids["assistant_message_id"]
    idea = client.post(
        f"/v1/threads/{thread_id}/branches",
        json={"name": "idea", "created_from_branch_id": main_id, "created_from_message_id": tip},
    ).json()
    idea_id = idea["id"]

    # diverge both
    _say(client, main_id, "main 2")
    _say(client, idea_id, "idea 2")

    # (Optional) if you added /v1/diff route, call it:
    # d = client.get(f"/v1/diff", params={"source_branch_id": idea_id, "target_branch_id": main_id})
    # assert d.status_code == 200
    # ds = d.json()
    # assert ds["lca"] is not None
    # assert len(ds["src_delta"]) >= 1
    # assert len(ds["tgt_delta"]) >= 1

    # merge: idea -> main
    m = client.post("/v1/merge", json={
        "thread_id": thread_id,
        "source_branch_id": idea_id,
        "target_branch_id": main_id,
        "strategy": "hybrid"
    })
    assert m.status_code == 200
    payload = m.json()
    assert "merge_id" in payload and "merged_into_message_id" in payload

    # target branch received a new assistant merge-commit
    msgs = client.get(f"/v1/branches/{main_id}/messages").json()
    # last message should be assistant + origin merge (origin not in response; check text)
    assert msgs[-1]["role"] == "assistant"
    assert "merge" in msgs[-1]["content"]["text"]
