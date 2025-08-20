from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import threads, branches, messages, merges, diff, edges

app = FastAPI(
    title="ConvoHub API",
    description="""
    ConvoHub is a conversation management system that supports branching, merging, and diffing of conversation threads.
    
    ## Features
    
    * **Threads**: Create and manage conversation threads
    * **Branches**: Fork conversations to explore different paths
    * **Messages**: Send messages and get AI responses
    * **Merging**: Merge divergent conversation branches
    * **Diffing**: Compare branches to see differences
    
    ## Authentication
    
    All endpoints require authentication. Include your API key in the Authorization header:
    `Authorization: Bearer your-api-key`
    
    ## Idempotency
    
    POST endpoints support idempotency keys to prevent duplicate operations. Include an `idempotency_key` in your request body.
    
    ## Pagination
    
    List endpoints support cursor-based pagination using the `cursor` and `limit` query parameters.
    """,
    version="0.1.0",
    contact={
        "name": "ConvoHub API Support",
        "email": "support@convohub.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "threads",
            "description": "Operations with conversation threads",
        },
        {
            "name": "branches", 
            "description": "Operations with conversation branches",
        },
        {
            "name": "messages",
            "description": "Operations with messages",
        },
        {
            "name": "merges",
            "description": "Operations for merging branches",
        },
        {
            "name": "diff",
            "description": "Operations for comparing branches",
        },
        {
            "name": "edges",
            "description": "Operations for managing message DAG edges",
        },
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import debug

from app.core.settings import settings
print("ENV:", settings.ENV)
print("DATABASE_URL:", settings.DATABASE_URL)
print("TEST_DATABASE_URL:", settings.TEST_DATABASE_URL)

@app.get("/health", tags=["health"])
def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Status indicating the service is healthy
    """
    return {"ok": True}

@app.get("/openapi.json", tags=["docs"])
def get_openapi():
    """
    Get the OpenAPI specification.
    
    Returns:
        dict: OpenAPI specification in JSON format
    """
    return app.openapi()

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
        }
    )

app.include_router(threads.router, prefix="/v1")
app.include_router(branches.router, prefix="/v1")
app.include_router(messages.router, prefix="/v1")
app.include_router(merges.router, prefix="/v1")
app.include_router(diff.router, prefix="/v1")
app.include_router(edges.router, prefix="/v1")
app.include_router(debug.router, prefix="/v1")

