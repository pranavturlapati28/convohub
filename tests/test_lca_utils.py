# tests/test_lca_utils.py
from app.merge_utils import find_lca, path_after, interleave_by_created_at
from app.models import Message, Branch, Thread
from uuid import uuid4
from datetime import datetime, timedelta

def test_lca_and_paths(db_session):
    # create a real thread (FK target)
    thread = Thread(
        id=str(uuid4()),
        owner_id=str(uuid4()),
        title="T",
        created_at=datetime.utcnow(),
    )
    db_session.add(thread)

    # branch under that thread
    br = Branch(
        id=str(uuid4()),
        thread_id=thread.id,   # <-- use the real thread id
        name="b",
        created_at=datetime.utcnow()
    )
    db_session.add(br)

    # messages
    t0 = datetime.utcnow()
    base = Message(id=str(uuid4()), branch_id=br.id, parent_message_id=None, role="system",
                   content={"text": "init"}, created_at=t0)
    a1 = Message(id=str(uuid4()), branch_id=br.id, parent_message_id=base.id, role="user",
                 content={"text": "a1"}, created_at=t0 + timedelta(seconds=1))
    a2 = Message(id=str(uuid4()), branch_id=br.id, parent_message_id=a1.id, role="assistant",
                 content={"text": "a2"}, created_at=t0 + timedelta(seconds=2))
    b1 = Message(id=str(uuid4()), branch_id=br.id, parent_message_id=base.id, role="user",
                 content={"text": "b1"}, created_at=t0 + timedelta(seconds=3))
    db_session.add_all([base, a1, a2, b1])
    db_session.commit()

    lca = find_lca(db_session, a2.id, b1.id)
    assert lca == base.id

    a_path = path_after(db_session, lca, a2.id)
    b_path = path_after(db_session, lca, b1.id)
    assert [m.id for m in a_path] == [a1.id, a2.id]
    assert [m.id for m in b_path] == [b1.id]

    merged = interleave_by_created_at(a_path, b_path)
    assert [m.id for m in merged] == [a1.id, a2.id, b1.id]
