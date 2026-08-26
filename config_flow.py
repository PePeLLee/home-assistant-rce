"""Config flow for RCE integration."""

from homeassistant import config_entries
from . import DOMAIN


class RCEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for RCE integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        await self.async_set_unique_id("rce_config_flow")
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Rynkowa Cena Energii",
                data={},
            )

        return self.async_show_form(step_id="user")
