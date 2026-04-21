from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# ✅ Add CORS middleware
# This allows your Next.js app (usually on port 3000) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'll change this to your specific URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Create /api/v1/health endpoint
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok", 
        "message": "Prompt Polisher Backend is Live!",
        "database": "Connected & Migrated"
    }

if __name__ == "__main__":
    import uvicorn
    # ✅ Verify uvicorn serves on localhost:8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)