@echo off
chcp 65001 >nul
cd /d "%~dp0"

title Archiwum Sprzedazy
echo ===================================================
echo     ARCHIWUM SPRZEDAZY (WERSJA GOOGLE DRIVE)
echo ===================================================
echo.

:: Szybki test czy srodowisko na TYM komputerze dziala prawidlowo
echo [1/3] Weryfikacja spersonalizowanego srodowiska dla Twojego komputera...
if exist ".venv\Scripts\python.exe" (
    .\.venv\Scripts\python.exe -c "import fastapi" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Srodowisko tego komputera jest w pelni sprawne!
        goto start_server
    ) else (
        echo [UWAGA] Wykryto brak pakietow lub zmiane komputera z Dysku Google!
        echo         Rozpoczynam szybka naprawe srodowiska lokalnego...
    )
) else (
    echo [UWAGA] Nie znaleziono srodowiska wirtualnego. Tworzenie go na nowo...
)

:: Proces Poszukiwania Pythona
set "PYTHON_EXE="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto build_env
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto build_env
)
for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%i\python.exe" (
        set "PYTHON_EXE=%%i\python.exe"
        goto build_env
    )
)
for /d %%i in ("C:\Program Files\Python*") do (
    if exist "%%i\python.exe" (
        set "PYTHON_EXE=%%i\python.exe"
        goto build_env
    )
)

:not_found
echo [BLAD KRYTYCZNY] Komputer na ktorym to uruchamiasz nie posiada zainstalowanego jezyka Python!
echo Pobierz go na ten komputer (z www.python.org), i zaznacz krateczke 'Add to PATH' w instalatorze.
pause
exit /b

:build_env
echo [2/3] Automatyczna naprawa uzywajac interpretera: %PYTHON_EXE%
echo       Trwa tworzenie srodowiska (.venv). Prosze czekac...
if exist ".venv" rmdir /S /Q ".venv"
"%PYTHON_EXE%" -m venv .venv

echo       Trwa instalowanie zaleznosci bazy danych...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r backend\requirements.txt >nul 2>&1

:start_server
echo.
echo [3/3] Uruchamianie silnika!
echo ===================================================
echo   PANEL ARCHIWUM DOSTEPNY POD TYM ADRESEM W PRZEGLADARCE:
echo   --^>  http://localhost:8001
echo ===================================================
echo   WAZNE: ZOSTAW TO CZARNE OKIENKO OTWARTE W TLE!
echo.
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
pause
