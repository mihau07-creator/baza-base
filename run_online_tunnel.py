import subprocess
import re
import sys
import os
import time
import signal

PYTHON_EXE = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

CLOUDFLARED_EXE = os.path.join(os.path.dirname(__file__), "cloudflared.exe")

print("=" * 65)
print("     ARCHIWUM SPRZEDAZY - BEZPOSREDNI DOSTEP ONLINE (TUNEL)")
print("=" * 65)
print("[1/2] Uruchamianie serwera bazy danych (FastAPI)...")

# 1. Start Uvicorn Server
uvicorn_proc = subprocess.Popen(
    [PYTHON_EXE, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=os.path.dirname(__file__),
    encoding="utf-8",
    errors="replace"
)

# Wait a moment for server to bind
time.sleep(2)

print("[2/2] Tworzenie bezpiecznego, szyfrowanego tunelu HTTPS przez Cloudflare...")

if not os.path.exists(CLOUDFLARED_EXE):
    print(f"[BLAD] Nie znaleziono pliku {CLOUDFLARED_EXE}!")
    uvicorn_proc.terminate()
    sys.exit(1)

# 2. Start Cloudflare Tunnel
tunnel_proc = subprocess.Popen(
    [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=os.path.dirname(__file__),
    encoding="utf-8",
    errors="replace"
)

tunnel_url = None
start_time = time.time()

# Watch output for trycloudflare URL
try:
    for line in iter(tunnel_proc.stdout.readline, ''):
        # Look for trycloudflare link
        match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
        if match and not tunnel_url:
            tunnel_url = match.group(1)
            print("\n" + "=" * 65)
            print("  SUKCES! TWOJA BAZA JEST W PELNI DOSTEPNA Z DOWOLNEGO MIEJSCA:")
            print(f"  -->  {tunnel_url}  <--")
            print("=" * 65)
            print("  Domyslne haslo: archiwum2025")
            print("  Mozesz otworzyc powyzszy link na telefonie, tablecie lub laptopie.")
            print("  Aby zakonczyc dzialanie, nacisnij Ctrl+C w tym oknie.")
            print("=" * 65 + "\n")
        
        # Check if uvicorn or tunnel died
        if uvicorn_proc.poll() is not None:
            print("[BLAD] Serwer uvicorn zakonczyl dzialanie!")
            break
        if tunnel_proc.poll() is not None:
            print("[BLAD] Tunel Cloudflare zakonczyl dzialanie!")
            break

except KeyboardInterrupt:
    print("\nZatrzymywanie uslug...")
finally:
    try:
        tunnel_proc.terminate()
    except: pass
    try:
        uvicorn_proc.terminate()
    except: pass
    print("Zakonczono pomyslnie.")
