from fastapi import FastAPI
from app.routers import threads, branches, messages, merges, diff

app = FastAPI(title="ConvoHub", version="0.1.0")

from app.routers import debug


from app.core.settings import settings
print("ENV:", settings.ENV)
print("DATABASE_URL:", settings.DATABASE_URL)
print("TEST_DATABASE_URL:", settings.TEST_DATABASE_URL)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(threads.router, prefix="/v1")
app.include_router(branches.router, prefix="/v1")
app.include_router(messages.router, prefix="/v1")
app.include_router(merges.router, prefix="/v1")
app.include_router(diff.router, prefix="/v1")
app.include_router(debug.router, prefix="/v1")

