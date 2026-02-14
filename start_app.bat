@echo off
cd /d "%~dp0"

echo Uruchamianie aplikacji Baza Base (Streamlit)...
echo Prosze nie zamykac tego okna.

:: Attempt to activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Ostrzezenie: Nie znaleziono srodowiska wirtualnego folderze .venv
    echo Sprobujemy uzyc globalnego pythona...
)

:: Streamlit automatically opens the browser, so we just run it
streamlit run app.py

pause
