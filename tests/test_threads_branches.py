# tests/test_threads_branches.py
def test_create_thread(client):
    r = client.post("/v1/threads", json={"title": "My Project"})
    assert r.status_code == 200
    data = r.json()
    assert "id" in data and data["title"] == "My Project"

def test_create_branch_seeds_system_message(client):
    t = client.post("/v1/threads", json={"title": "T"}).json()
    b = client.post(f"/v1/threads/{t['id']}/branches", json={"name": "main"}).json()
    msgs = client.get(f"/v1/branches/{b['id']}/messages").json()
    assert len(msgs) >= 1
    assert msgs[0]["role"] == "system"
