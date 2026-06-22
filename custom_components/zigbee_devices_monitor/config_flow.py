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
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector

from .const import (
    CONF_EXCLUDED_DEVICES,
    CONF_SCAN_INTERVAL,
    CONF_UNAVAILABLE_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNAVAILABLE_TIMEOUT,
    DOMAIN,
    ZIGBEE_INTEGRATION_DOMAINS,
)


def _get_zigbee_device_options(
    hass: HomeAssistant,
) -> list[selector.SelectOptionDict]:
    """Return sorted list of Zigbee device select options."""
    device_reg = dr.async_get(hass)
    entry_ids = {
        entry.entry_id
        for entry in hass.config_entries.async_entries()
        if entry.domain in ZIGBEE_INTEGRATION_DOMAINS
    }
    options: list[selector.SelectOptionDict] = []
    for device in device_reg.devices.values():
        if any(eid in entry_ids for eid in device.config_entries):
            name = device.name_by_user or device.name or str(device.id)
            options.append(selector.SelectOptionDict(value=device.id, label=name))
    return sorted(options, key=lambda x: x["label"])


def _build_schema(
    hass: HomeAssistant,
    defaults: dict[str, Any],
) -> vol.Schema:
    """Build config schema."""
    device_options = _get_zigbee_device_options(hass)
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
            vol.Optional(
                CONF_EXCLUDED_DEVICES,
                default=defaults.get(CONF_EXCLUDED_DEVICES, []),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=device_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
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
            CONF_EXCLUDED_DEVICES: [],
        }
        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(self.hass, defaults),
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow."""
        return ZigbeeDevicesMonitorOptionsFlow()


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
            CONF_EXCLUDED_DEVICES: self.config_entry.options.get(
                CONF_EXCLUDED_DEVICES,
                self.config_entry.data.get(CONF_EXCLUDED_DEVICES, []),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(self.hass, defaults),
        )
