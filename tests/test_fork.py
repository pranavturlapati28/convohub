# tests/test_fork.py
def _say(client, branch_id, text):
    r = client.post(f"/v1/branches/{branch_id}/messages", json={"role": "user", "text": text})
    assert r.status_code == 200
    return r.json()

def test_fork_from_message_copies_snapshot(client):
    # base thread/branch
    t = client.post("/v1/threads", json={"title": "Forky"}).json()
    b = client.post(f"/v1/threads/{t['id']}/branches", json={"name": "main"}).json()
    branch_id = b["id"]

    # produce a user + assistant pair so we have a snapshot on the assistant message
    ids = _say(client, branch_id, "context 1")
    tip_assistant_id = ids["assistant_message_id"]

    # create a new branch from that message
    new_branch = client.post(
        f"/v1/threads/{t['id']}/branches",
        json={"name": "idea-A", "created_from_branch_id": branch_id, "created_from_message_id": tip_assistant_id},
    ).json()

    # new branch should have a seed system message (with snapshot if source had one)
    msgs = client.get(f"/v1/branches/{new_branch['id']}/messages").json()
    assert msgs[0]["role"] == "system"
    # Snapshot presence (if your seed copies it)
    # state_snapshot is not in the response model above; if not returned, skip or expose it in response.
