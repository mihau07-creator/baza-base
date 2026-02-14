# Publikacja online (Streamlit Cloud)

Aby Twoja aplikacja była dostępna z każdego miejsca, możesz skorzystać z darmowej usługi **Streamlit Community Cloud**.

## Krok 1: Przygotowanie danych

Aby aplikacja w chmurze miała dostęp do Twoich danych, plik `sales.db` musi znaleźć się na GitHubie.
(Ten krok wykonałem już automatycznie, usuwając go z ignorowanych plików).

## Krok 2: Rejestracja i połączenie

1. Wejdź na stronę [share.streamlit.io](https://share.streamlit.io/).
2. Zaloguj się (najlepiej używając konta GitHub).
3. Kliknij przycisk **"New app"** (prawy górny róg).
4. Wybierz opcję **"Use existing repo"**.

## Krok 3: Konfiguracja aplikacji

W formularzu wybierz:
- **Repository**: `michallytka/baza-base`
- **Branch**: `main`
- **Main file path**: `app.py`

Kliknij **"Deploy!"**.

## Częste pytania

### Czy muszę mieć włączony komputer?
**NIE.** Jeśli skorzystasz z Streamlit Cloud, Twoja aplikacja i baza danych działają na zewnętrznych serwerach. Możesz wyłączyć swój komputer, a nadal będziesz mieć podgląd danych na telefonie czy tablecie.

### Jak zaktualizować dane?
Ponieważ baza danych w chmurze jest "kopią" Twojej lokalnej bazy, nowe zamówienia dodane na komputerze nie pojawią się automatycznie online. Aby je zaktualizować:

1. Dodaj nowe dane do bazy na swoim komputerze (tak jak zwykle).
2. Kliknij dwukrotnie plik `github_upload.bat`.
3. Poczekaj kilka minut – aplikacja w chmurze sama pobierze nową wersję bazy.

> [!WARNING]
> Jeśli dodasz dane przez stronę internetową (w chmurze), mogą one zniknąć po restarcie aplikacji. Traktuj wersję online jako "tylko do odczytu" (podgląd), a dane dodawaj zawsze na swoim komputerze.
