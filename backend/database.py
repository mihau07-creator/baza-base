from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "sales.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

raw_db_url = os.getenv("DATABASE_URL", "").strip()

if not raw_db_url:
    target_url = DEFAULT_SQLITE_URL
elif raw_db_url.startswith("postgres://"):
    target_url = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    target_url = raw_db_url

def create_db_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, connect_args={"connect_timeout": 5}, pool_pre_ping=True)

engine = None

if not target_url.startswith("sqlite"):
    try:
        candidate_engine = create_db_engine(target_url)
        with candidate_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = candidate_engine
        print("[DATABASE] Polaczono pomyslnie z baza PostgreSQL!")
    except Exception as err:
        print(f"[DATABASE WARNING] Blad polaczenia z PostgreSQL ({err}).")
        print(f"[DATABASE INFO] Bezpieczne przelaczenie na baze lokalna SQLite: {DEFAULT_SQLITE_PATH}")
        engine = create_db_engine(DEFAULT_SQLITE_URL)
else:
    engine = create_db_engine(target_url)
    print(f"[DATABASE INFO] Uruchomiono baze SQLite: {target_url}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
