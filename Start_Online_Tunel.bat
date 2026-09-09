@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Archiwum Sprzedazy - Dostep Online (Tunel Cloudflare)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_online_tunnel.py
) else (
    python run_online_tunnel.py
)

pause
