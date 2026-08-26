"""Constants for the RCE integration."""

from datetime import timedelta

DOMAIN = "rce"
PLATFORMS = ["calendar", "sensor"]

# API Configuration
PSE_API_URL_TODAY = "https://api.raporty.pse.pl/api/rce-pln"
PSE_API_URL_TOMORROW = "https://apimpdv2-bmgdhhajexe8aade.a01.azurefd.net/api/rce-pln"
PSE_INFO_URL = (
    "https://www.pse.pl/dane-systemowe/funkcjonowanie-rb/raporty-dobowe-z-funkcjonowania-rb/"
    "podstawowe-wskazniki-cenowe-i-kosztowe/rynkowa-cena-energii-elektrycznej-rce"
)

# Timing
SCAN_INTERVAL = timedelta(hours=1)  # Try every hour (smart retry)
REQUEST_TIMEOUT = 10  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 300  # 5 minutes
