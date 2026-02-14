@echo off
cd /d "%~dp0"
echo Konfigurowanie i wysylanie na GitHub (https://github.com/michallytka/baza-base.git)...

:: Remove origin if it exists to ensure we set the new one correctly
git remote remove origin 2>nul

:: Add the remote
git remote add origin https://github.com/michallytka/baza-base.git

:: Rename branch to main just in case
git branch -M main

:: Add all changes
echo Dodawanie zmienionych plikow...
git add .

:: Commit changes
echo Zatwierdzanie zmian...
git commit -m "Automatyczna aktualizacja"

:: Push to the repository
echo Wysylanie plikow...
git push -u origin main

if %errorlevel% neq 0 (
    echo Wystapil blad podczas wysylania. Sprawdz czy masz dostep do internetu i czy podane dane logowania sa poprawne.
    echo Jesli zmieniles konto GitHub, moze byc konieczne wyczyszczenie starych poswiadczen w Systemie Windows (Menedzer poswiadczen).
) else (
    echo Sukces! Pliki zostaly wyslane.
)

pause
