import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Konieczne, żeby model załadował się do Base.metadata
from backend.models import Base

load_dotenv()

# Old Engine (SQLite)
sqlite_engine = create_engine(r"sqlite:///C:\Users\moled\Antigravity\Baza Base\sales.db")

# New Engine (Supabase Postgres)
supabase_url = os.getenv("DATABASE_URL")
if supabase_url.startswith("postgres://"):
    supabase_url = supabase_url.replace("postgres://", "postgresql://", 1)

postgres_engine = create_engine(supabase_url)

print("Tworzenie pustych, powiazanych tabel w chmurze (PostgreSQL)...")
Base.metadata.create_all(bind=postgres_engine)

print("Pobieranie i kopiowanie zamowien (Orders)...")
orders_df = pd.read_sql_table("orders", sqlite_engine)
orders_df.to_sql("orders", postgres_engine, if_exists="append", index=False, chunksize=1000)

print("Pobieranie i kopiowanie przedmiotow (Items)...")
items_df = pd.read_sql_table("items", sqlite_engine)
items_df.to_sql("items", postgres_engine, if_exists="append", index=False, chunksize=1000)

print("Aktualizowanie auto-inkrementacji w bazie...")
with postgres_engine.connect() as conn:
    conn.execute(text("SELECT setval(pg_get_serial_sequence('items', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM items;"))
    conn.commit()

print(f"Migracja zakonczona gigantycznym sukcesem! Przeniesiono {len(orders_df)} zamowien.")
