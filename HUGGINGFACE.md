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
   - **Soce SDK**: Wybierz **Streamlit**.
   - **Space hardware**: Wybierz **Free** (CPU basic).
   - **Privacy**: Wybierz **Public** (jeśli chcesz mieć łatwy dostęp) lub **Private** (wymaga logowania).
5. Kliknij **Create Space**.

## Krok 3: Połączenie z kodem

Masz teraz puste "Space". Musimy tam wgrać Twój kod.
Dla początkujących najłatwiej jest **zrobić to ręcznie** (upload) lub **połączyć z GitHubem**.

### Opcja A: Połączenie z GitHub (Zalecane)
1. W ustawieniach Space (zakładka **Settings** na górze strony space'a).
2. Znajdź sekcję **"Git Repository"** lub **"Sync with GitHub"**.
3. Połącz ze swoim repozytorium: `michallytka/baza-base`.

### Opcja B: Szybki start (gdyby opcja A była trudna)
1. Na stronie Space wejdź w zakładkę **Files**.
2. Kliknij **"Add file"** -> **"Upload files"**.
3. Przeciągnij tam pliki: `app.py`, `sales.db`, `requirements.txt` oraz folder `backend` (jeśli się da, lub stwórz go i wgraj `models.py`).
4. Kliknij **Commit changes**.

Aplikacja powinna się zbudować i uruchomić w ciągu kilku minut.
