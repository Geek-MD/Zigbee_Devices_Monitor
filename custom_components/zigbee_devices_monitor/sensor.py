"""Sensor platform for Zigbee Devices Monitor."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

DEFAULT_NAME = "Zigbee Devices Warning"
DEFAULT_UNAVAILABLE_TIMEOUT = 300
DEFAULT_ZIGBEE_DOMAIN = "zha"
DEFAULT_SCAN_INTERVAL = 30

CONF_UNAVAILABLE_TIMEOUT = "unavailable_timeout"
CONF_ZIGBEE_DOMAIN = "zigbee_domain"
CONF_SCAN_INTERVAL = "scan_interval"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNAVAILABLE_TIMEOUT, default=DEFAULT_UNAVAILABLE_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_ZIGBEE_DOMAIN, default=DEFAULT_ZIGBEE_DOMAIN): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up the Zigbee warning sensor."""
    async_add_entities(
        [
            ZigbeeWarningSensor(
                hass,
                config[CONF_NAME],
                config[CONF_UNAVAILABLE_TIMEOUT],
                config[CONF_ZIGBEE_DOMAIN],
                config[CONF_SCAN_INTERVAL],
            )
        ],
        True,
    )


class ZigbeeWarningSensor(SensorEntity):
    """Monitor Zigbee entities and report unavailability warnings."""

    _attr_icon = "mdi:alert"

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        unavailable_timeout: int,
        zigbee_domain: str,
        scan_interval: int,
    ) -> None:
        self._hass = hass
        self._attr_name = name
        self._attr_unique_id = f"zigbee_warning_{zigbee_domain}"
        self._attr_should_poll = False
        self._timeout = timedelta(seconds=unavailable_timeout)
        self._timeout_seconds = unavailable_timeout
        self._zigbee_domain = zigbee_domain
        self._scan_interval = scan_interval
        self._unavailable_since: dict[str, float] = {}
        self._unavailable_devices: list[str] = []
        self._cancel_interval: Callable[[], None] | None = None

    @property
    def native_value(self) -> str:
        """Return warning status."""
        return "warning" if self._unavailable_devices else "ok"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return details for unavailable devices."""
        return {
            "zigbee_domain": self._zigbee_domain,
            "timeout_seconds": self._timeout_seconds,
            "scan_interval": self._scan_interval,
            "unavailable_count": len(self._unavailable_devices),
            "unavailable_devices": self._unavailable_devices,
        }

    async def async_added_to_hass(self) -> None:
        """Register periodic updates."""
        self._cancel_interval = async_track_time_interval(
            self._hass,
            self._async_update_from_states,
            timedelta(seconds=self._scan_interval),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners."""
        if self._cancel_interval:
            self._cancel_interval()

    @callback
    def _async_update_from_states(self, _now: datetime) -> None:
        """Process tracked states and write entity state."""
        self._process_states()
        self.async_write_ha_state()

    def _process_states(self) -> None:
        """Update unavailable entities list based on timeout."""
        current_time = self._hass.loop.time()
        zigbee_entities = self._get_zigbee_entities()

        for entity_id in zigbee_entities:
            state = self._hass.states.get(entity_id)
            if state and state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                self._unavailable_since.setdefault(entity_id, current_time)
            else:
                self._unavailable_since.pop(entity_id, None)

        self._unavailable_since = {
            entity_id: since
            for entity_id, since in self._unavailable_since.items()
            if entity_id in zigbee_entities
        }

        self._unavailable_devices = sorted(
            [
                entity_id
                for entity_id, since in self._unavailable_since.items()
                if (current_time - since) >= self._timeout.total_seconds()
            ]
        )

    def _get_zigbee_entities(self) -> set[str]:
        """Get entities bound to the configured Zigbee integration domain."""
        registry = er.async_get(self._hass)
        zigbee_entities: set[str] = set()

        for entity in registry.entities.values():
            if entity.disabled_by is not None:
                continue

            config_entry_id = entity.config_entry_id
            if not config_entry_id:
                continue

            config_entry = self._hass.config_entries.async_get_entry(config_entry_id)
            if config_entry and config_entry.domain == self._zigbee_domain:
                zigbee_entities.add(entity.entity_id)

        return zigbee_entities
