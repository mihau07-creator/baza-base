# Publikacja online (Streamlit Cloud)

Aby Twoja aplikacja była dostępna z każdego miejsca, możesz skorzystać z darmowej usługi **Streamlit Community Cloud**.

## Krok 1: Przygotowanie danych

Aby aplikacja w chmurze miała dostęp do Twoich danych, plik `sales.db` musi znaleźć się na GitHubie.
(Ten krok wykonałem już automatycznie, usuwając go z ignorowanych plików).

Pamiętaj:
> [!WARNING]
> System plików na Streamlit Cloud jest "ulotny". Oznacza to, że jeśli dodasz nowe zamówienia przez stronę internetową, mogą one zniknąć po restarcie aplikacji.
> Najbezpieczniej jest dodawać dane lokalnie na komputerze, a następnie wysyłać zaktualizowany plik `sales.db` na GitHub za pomocą skryptu `github_upload.bat`.

## Krok 2: Rejestracja i połączenie

1. Wejdź na stronę [share.streamlit.io](https://share.streamlit.io/).
2. Zaloguj się (najlepiej używając konta GitHub).
3. Kliknij przycisk **"New app"** (prawy górny róg).
4. Wybierz opcję **"Use existing repo"**.

## Krok 3: Konfiguracja aplikacji

W formularzu wybierz:
- **Repository**: `mihau07-creator/baza-base`
- **Branch**: `main`
- **Main file path**: `app.py`

Kliknij **"Deploy!"**.

## Gotowe!

Po kilku minutach Twoja aplikacja będzie dostępna pod adresem internetowym, który możesz wysłać komukolwiek lub otworzyć na telefonie.

## Aktualizacja danych

Gdy dodasz nowe dane na komputerze:
1. Uruchom `github_upload.bat`.
2. Aplikacja w chmurze zaktualizuje się automatycznie po wykryciu zmian na GitHubie (może to potrwać kilka minut).
