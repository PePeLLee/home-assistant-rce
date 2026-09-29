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

## Przykładowe czujniki

### Sensor: Najtańsze okno 4 godzin

Poniżej przykład konfiguracji sensora, który automatycznie wyszukuje najtańsze 4-godzinne okno czasowe w bieżącym dniu:

```yaml
- trigger:
  - trigger: time
    at: "00:01:00"
  - trigger: homeassistant
    event: start
  action:
  - action: calendar.get_events
    target:
      entity_id: calendar.rce_calendar
    data:
      start_date_time: "{{ today_at('00:00:00') }}"
      duration:
        hours: 24
    response_variable: rce_events
  sensor:
  - name: Najtansze okno RCE 4h
    unique_id: najtansze_okno_rce_4h
    device_class: timestamp
    state: >-
      {% set events = rce_events['calendar.rce_calendar'].events if rce_events is defined and 'calendar.rce_calendar' in rce_events else [] %}
      {% if events | length >= 16 %}
        {% set ns = namespace(min_avg=999999, best_start='') %}
        {% for i in range(0, events | length - 15) %}
          {% set window = events[i:i+16] %}
          {% set avg = (window | map(attribute='summary') | map('regex_findall', '([0-9]+\\.?[0-9]*)') | map('first') | map('float') | sum) / 16 %}
          {% if avg < ns.min_avg %}
            {% set ns.min_avg = avg %}
            {% set ns.best_start = window[0].start %}
          {% endif %}
        {% endfor %}
        {{ ns.best_start | as_datetime if ns.best_start else now() }}
      {% else %}
        {{ now() }}
      {% endif %}
    attributes:
      srednia_cena: >-
        {% set events = rce_events['calendar.rce_calendar'].events if rce_events is defined and 'calendar.rce_calendar' in rce_events else [] %}
        {% if events | length >= 16 %}
          {% set ns = namespace(min_avg=999999) %}
          {% for i in range(0, events | length - 15) %}
            {% set window = events[i:i+16] %}
            {% set avg = (window | map(attribute='summary') | map('regex_findall', '([0-9]+\\.?[0-9]*)') | map('first') | map('float') | sum) / 16 %}
            {% if avg < ns.min_avg %}
              {% set ns.min_avg = avg %}
            {% endif %}
          {% endfor %}
          {{ ns.min_avg | round(2) }}
        {% else %}
          unknown
        {% endif %}
```
Sensor ten:

- Uruchamia się codziennie o 00:01 oraz przy starcie Home Assistant
- Pobiera wszystkie wydarzenia z kalendarza RCE na bieżący dzień
- Wyszukuje 4-godzinne okno (16 kwadransów co 15 minut) z najniższą średnią ceną
- Wyświetla datę i godzinę rozpoczęcia najtańszego okna
- Przechowuje średnią cenę w atrybucie srednia_cena

## Zrzuty ekranu

![Konfiguracja](https://github.com/PePeLLee/home-assistant-rce/assets/61408245/2fd4b0e5-10ac-48d8-9072-c141a9c8f838)

![Widok kalendarza](https://github.com/PePeLLee/home-assistant-rce/assets/61408245/fb708945-b5b4-4eb9-a991-c913a078aba0)

## Wkład i rozwój
Jeśli chcesz zgłosić błąd lub zaproponować poprawkę — otwórz issue lub pull request w tym repozytorium.

## Licencja
Repozytorium nie zawiera jawnie zdefiniowanej licencji — jeśli chcesz używać integracji w projekcie publicznym, skontaktuj się z autorem repozytorium.

---

Autor: PePeLLee
