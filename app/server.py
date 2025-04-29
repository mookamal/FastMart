from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routers import auth_router
from app.api.graphql.router import graphql_router

app = FastAPI(title="Analytic Project API")

origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Analytic Project API"}

# Optional: Add logic to run the server directly for development
if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)