import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

from database import engine, Base
from routers import upload, generate, upload_and_generate

# create DB tables (simple approach for prototype)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Question Generation Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(generate.router, prefix="/generate", tags=["generate"])
app.include_router(upload_and_generate.router, prefix="/api", tags=["combined"])

@app.get("/")
async def root():
    return {"status": "ok"}
