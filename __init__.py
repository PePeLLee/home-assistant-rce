"""The example sensor integration."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import SOURCE_SYSTEM, ConfigEntry

DOMAIN = "rce"
async def async_setup(hass: HomeAssistant, config):
    """Wstepna konfiguracja domeny, jeśli to konieczne."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Konfigurowanie integracji na podstawie wpisu konfiguracyjnego."""
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setup(config_entry, "calendar")
    # )
    await hass.config_entries.async_forward_entry_setups(entry, [ "calendar" ] )
    return True

async def async_unload_entry(hass: HomeAssistant,  entry: ConfigEntry):
    """Usunięcie integracji - skasowanie wpis konfiguracyjnego ."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [ "calendar" ] )
    return unload_ok
