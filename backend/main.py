import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models, api

# Safe database tables initialization
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"[MAIN WARNING] Blad podczas Base.metadata.create_all: {e}")

app = FastAPI(title="Sales Archive")

app.include_router(api.router)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Absolute path for static files (Frontend)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
