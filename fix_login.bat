@echo off
echo Czyszczenie zapisanych hasel do GitHub...
cmdkey /delete:git:https://github.com
echo.
echo Gotowe. Teraz uruchom github_upload.bat ponownie.
echo Zostaniesz poproszony o ponowne zalogowanie sie.
pause
