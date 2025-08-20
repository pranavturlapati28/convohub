from fastapi import Depends, HTTPException, status

class User:
    def __init__(self, id: str): self.id = id

def get_current_user():
    # MVP: one fake user
    return User(id="00000000-0000-0000-0000-000000000001")
