# Baza Base - Archiwum Sprzedaży

Aplikacja do przeglądania i analizy archiwum sprzedaży, zbudowana w oparciu o [Streamlit](https://streamlit.io).

## Uruchomienie

Aby uruchomić aplikację:
1. Kliknij dwukrotnie plik `start_app.bat` w folderze głównym.
2. Aplikacja powinna otworzyć się automatycznie w przeglądarce.

## Instalacja na GitHub

Aby wysłać projekt na GitHub:
1. Uruchom plik `github_upload.bat`.
2. Jeśli zostaniesz poproszony o zalogowanie się, postępuj zgodnie z instrukcjami w oknie.

Adres repozytorium: https://github.com/michallytka/baza-base.git

## Struktura

- `app.py`: Główny plik aplikacji (interfejs i logika).
- `github_upload.bat`: Skrypt do automatycznej wysyłki na GitHub.
- `start_app.bat`: Skrypt uruchamiający aplikację.
- `backend/models.py`: Definicje tabel bazy danych.
- `sales.db`: Plik bazy danych SQLite (nie jest wysyłany na GitHub jeśli dodany do .gitignore, co jest zalecane dla prywatnych danych).

## Wymagania

- Python 3.8+
- Biblioteki z pliku `requirements.txt`:
    - streamlit
    - pandas
    - sqlalchemy
    - plotly
