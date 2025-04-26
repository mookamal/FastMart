from fastapi import FastAPI
import uvicorn

from app.api.routers import auth_router

app = FastAPI(title="Analytic Project API")

# Include routers
app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Analytic Project API"}

# Optional: Add logic to run the server directly for development
if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)