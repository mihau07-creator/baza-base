# Alternatywa: Hugging Face Spaces

Jeśli Streamlit Cloud zablokował Twoje konto ("Error: Your account has exceeded the fair-use limits..."), najlepszą darmową alternatywą jest **Hugging Face Spaces**.

Działa to bardzo podobnie i też jest darmowe.

## Krok 1: Wyślij poprawki na GitHub

(Ważne: dodałem specjalną konfigurację do pliku README, którą musisz wysłać).

1. Uruchom `github_upload.bat`.

## Krok 2: Uruchomienie na Hugging Face

1. Wejdź na [huggingface.co/spaces](https://huggingface.co/spaces).
2. Zarejestruj się (Sign Up) – to darmowe.
3. Kliknij **Create new Space**.
4. Wypełnij formularz:
   - **Space name**: np. `baza-base`.
   - **License**: Wybierz cokolwiek, np. `mit`.
   - **Soce SDK**: Wybierz **Docker** (skoro Streamlit nie jest dostępny).
   - **Space hardware**: Wybierz **Free** (CPU basic).
   - **Privacy**: Wybierz **Public** (jeśli chcesz mieć łatwy dostęp) lub **Private** (wymaga logowania).
5. Kliknij **Create Space**.

## Krok 3: Połączenie z kodem

Masz teraz puste "Space". Musimy tam wgrać Twój kod.
Dla początkujących najłatwiej jest **zrobić to ręcznie** (upload) lub **połączyć z GitHubem**.

### Opcja A: Połączenie z GitHub (Ukryte w Settings)
1. Wejdź w zakładkę **Settings** (na górze, obok nazwy Space'a, obok Files/App).
2. Przewiń w dół do sekcji **"Git Repository"**.
3. Wpisz tam adres swojego repozytorium: `https://github.com/michallytka/baza-base`.
4. Kliknij Connect.

### Opcja B: Ręczne wgranie plików (PROSTSZE)
Jeśli nie widzisz opcji A, zrób to ręcznie:
1. Wejdź w zakładkę **Files and versions** (na górze strony Space'a).
2. Kliknij **Add file** -> **Upload files**.
3. Przeciągnij z folderu na komputerze te pliki:
   - `Dockerfile`
   - `app.py`
   - `requirements.txt`
   - `sales.db`
   - `sales.db`

4. Kliknij **Commit changes**.

**Co zrobić z folderem `backend`?**
Hugging Face nie pozwala przeciągnąć całego folderu. Musisz stworzyć pliki ręcznie w środku folderu:
1. Kliknij **Add file** -> **Create new file**.
2. W nazwie pliku wpisz: `backend/models.py` (tak, z ukośnikiem!).
3. Wklej zawartość pliku `backend/models.py` z Twojego komputera.
4. Kliknij **Commit**.
5. Powtórz to dla `backend/database.py` i `backend/__init__.py`.

Aplikacja powinna się zbudować i uruchomić w ciągu kilku minut.
