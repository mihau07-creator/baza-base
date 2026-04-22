@echo off
chcp 65001 >nul
cd /d "%~dp0"

title Importer Archiwum (Supabase)
echo ===================================================
echo   WYSYLANIE NOWYCH ZAMOWIEN DO CHMURY (SUPABASE)
echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [BLAD] Nie znaleziono srodowiska pythona!
    pause
    exit /b
)

echo Nawiązywanie bezpiecznego polaczenia...
.\.venv\Scripts\python.exe -m backend.importer "BaseLinker Backup"

echo.
echo ===================================================
echo Gotowe! Wszystkie nowe zamowienia sa juz online!
echo ===================================================
pause
