# home-assistant-rce

Integracja dla Home Assistant udostępniająca dane o Rynkowej Cenie Energii Elektrycznej (RCE) publikowane przez PSE.

Źródło danych:
https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce

## Funkcjonalność
- Pobiera dzienne wartości RCE ze strony PSE
- Udostępnia integrację jako kalendarz w Home Assistant

## Wymagania
- Home Assistant (wersja obsługująca custom integrations)

## Instalacja
1. Skopiuj katalog `custom_components/rce` do katalogu `config/custom_components/` Twojej instalacji Home Assistant.
2. Zrestartuj Home Assistant.
3. W Home Assistant przejdź do Ustawienia -> Integracje -> Dodaj integrację i wyszukaj "RCE" — dodaj integrację przez UI (nie przez edycję konfiguracji YAML).

> Uwaga: Integracja jest instalowana jako custom component — upewnij się, że katalog `custom_components/rce` zawiera pliki z repozytorium.

## Konfiguracja
- Integracja nie wymaga ręcznej edycji pliku `configuration.yaml`. Wszystkie ustawienia wykonuje się przez interfejs użytkownika integracji po jej dodaniu.

## Użytkowanie
- Po dodaniu integracji w Home Assistant pojawi się encja typu kalendarz, w której dostępne będą wpisy z RCE dla kolejnych dni.

## Zrzuty ekranu

![Konfiguracja](https://github.com/PePeLLee/home-assistant-rce/assets/61408245/2fd4b0e5-10ac-48d8-9072-c141a9c8f838)

![Widok kalendarza](https://github.com/PePeLLee/home-assistant-rce/assets/61408245/fb708945-b5b4-4eb9-a991-c913a078aba0)

## Wkład i rozwój
Jeśli chcesz zgłosić błąd lub zaproponować poprawkę — otwórz issue lub pull request w tym repozytorium.

## Licencja
Repozytorium nie zawiera jawnie zdefiniowanej licencji — jeśli chcesz używać integracji w projekcie publicznym, skontaktuj się z autorem repozytorium.

---

Autor: PePeLLee
