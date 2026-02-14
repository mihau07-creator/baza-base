from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models, api

# Create database tables
models.Base.metadata.create_all(bind=engine)

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

# Placeholder for static files (Frontend will be built here later)
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
