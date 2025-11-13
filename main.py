from fastapi import FastAPI
from .routes import router as api_router
from .config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Resume Analyzer Backend (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # in prod restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message":"Resume Analyzer Backend (FastAPI)"}
