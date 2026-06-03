"""Config flow for Zigbee Devices Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNAVAILABLE_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNAVAILABLE_TIMEOUT,
    DOMAIN,
)


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build config schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): str,
            vol.Required(
                CONF_UNAVAILABLE_TIMEOUT,
                default=defaults[CONF_UNAVAILABLE_TIMEOUT],
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults[CONF_SCAN_INTERVAL],
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )


# Home Assistant uses `domain=` as a class keyword argument at declaration time,
# which mypy flags even though this is the framework's documented pattern.
class ZigbeeDevicesMonitorConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Zigbee Devices Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_UNAVAILABLE_TIMEOUT: DEFAULT_UNAVAILABLE_TIMEOUT,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(defaults),
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return ZigbeeDevicesMonitorOptionsFlow(config_entry)


class ZigbeeDevicesMonitorOptionsFlow(OptionsFlow):
    """Handle options for Zigbee Devices Monitor."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {
            CONF_NAME: self.config_entry.options.get(
                CONF_NAME, self.config_entry.data.get(CONF_NAME, DEFAULT_NAME)
            ),
            CONF_UNAVAILABLE_TIMEOUT: self.config_entry.options.get(
                CONF_UNAVAILABLE_TIMEOUT,
                self.config_entry.data.get(
                    CONF_UNAVAILABLE_TIMEOUT, DEFAULT_UNAVAILABLE_TIMEOUT
                ),
            ),
            CONF_SCAN_INTERVAL: self.config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults),
        )
