from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database import engine, Base
from app.routers import setup_router, goals_router, analysis_router, debug_router, revision_router, plan_router, chat_router

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(setup_router, tags=["Setup"])
app.include_router(goals_router, tags=["Goals"])
app.include_router(analysis_router, tags=["Analysis"])
app.include_router(debug_router, tags=["Debug"])
app.include_router(revision_router, tags=["Revision"])
app.include_router(plan_router, tags=["Plan"])
app.include_router(chat_router, tags=["Chat"])



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
