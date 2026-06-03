"""Sensor platform for Zigbee Devices Monitor."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UNAVAILABLE_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNAVAILABLE_TIMEOUT,
    ZIGBEE_INTEGRATION_DOMAINS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zigbee warning sensor from a config entry."""
    # Options are user-edited values and must override initial entry data.
    values = {**config_entry.data, **config_entry.options}
    async_add_entities(
        [
            ZigbeeWarningSensor(
                hass=hass,
                name=str(values.get(CONF_NAME, DEFAULT_NAME)),
                unavailable_timeout=int(
                    values.get(CONF_UNAVAILABLE_TIMEOUT, DEFAULT_UNAVAILABLE_TIMEOUT)
                ),
                scan_interval=int(values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            )
        ],
        True,
    )


class ZigbeeWarningSensor(SensorEntity):
    """Monitor Zigbee devices and report unavailability warnings."""

    _attr_icon = "mdi:alert"
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        unavailable_timeout: int,
        scan_interval: int,
    ) -> None:
        self._hass = hass
        self._attr_name = name
        self._attr_unique_id = "zigbee_devices_monitor_warning"
        self._timeout = timedelta(seconds=unavailable_timeout)
        self._timeout_seconds = unavailable_timeout
        self._scan_interval = scan_interval
        self._unavailable_since: dict[str, float] = {}
        self._unavailable_devices: list[str] = []
        self._detected_integrations: list[str] = []
        self._cancel_interval: Callable[[], None] | None = None

    @property
    def native_value(self) -> str:
        """Return warning status."""
        return "warning" if self._unavailable_devices else "ok"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return details for unavailable devices."""
        return {
            "detected_integrations": self._detected_integrations,
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

    def _detect_integrations(self) -> list[str]:
        """Return sorted list of detected Zigbee integration domains."""
        detected: list[str] = []
        for entry in self._hass.config_entries.async_entries():
            if entry.domain in ZIGBEE_INTEGRATION_DOMAINS and entry.domain not in detected:
                detected.append(entry.domain)
        return sorted(detected)

    def _get_zigbee_device_map(
        self,
    ) -> tuple[dict[str, str], dict[str, list[str]]]:
        """Return (device_names, device_entities) for all active Zigbee devices.

        device_names  – device_id → human-readable name
        device_entities – device_id → list of non-disabled entity_ids
        """
        device_reg = dr.async_get(self._hass)
        entity_reg = er.async_get(self._hass)

        zigbee_entry_ids: set[str] = set()
        for entry in self._hass.config_entries.async_entries():
            if entry.domain in ZIGBEE_INTEGRATION_DOMAINS:
                zigbee_entry_ids.add(entry.entry_id)

        if not zigbee_entry_ids:
            return {}, {}

        device_names: dict[str, str] = {}
        device_entities: dict[str, list[str]] = {}

        for device in device_reg.devices.values():
            if any(eid in zigbee_entry_ids for eid in device.config_entries):
                name = device.name_by_user or device.name or str(device.id)
                device_names[device.id] = name
                device_entities[device.id] = []

        for entity in entity_reg.entities.values():
            if entity.disabled_by is not None:
                continue
            if entity.device_id in device_entities:
                device_entities[entity.device_id].append(entity.entity_id)

        # Discard devices that have no trackable entities
        valid = {did for did, entities in device_entities.items() if entities}
        return (
            {did: name for did, name in device_names.items() if did in valid},
            {did: ents for did, ents in device_entities.items() if did in valid},
        )

    def _is_device_offline(self, entity_ids: list[str]) -> bool:
        """Return True when all entities of a device are unavailable or unknown."""
        if not entity_ids:
            return False
        return all(
            (s := self._hass.states.get(eid)) is not None
            and s.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            for eid in entity_ids
        )

    def _process_states(self) -> None:
        """Update offline devices list based on timeout."""
        current_time = self._hass.loop.time()
        self._detected_integrations = self._detect_integrations()
        device_names, device_entities = self._get_zigbee_device_map()

        for device_id, entity_ids in device_entities.items():
            if self._is_device_offline(entity_ids):
                self._unavailable_since.setdefault(device_id, current_time)
            else:
                self._unavailable_since.pop(device_id, None)

        # Remove stale entries for devices no longer in the registry
        self._unavailable_since = {
            did: since
            for did, since in self._unavailable_since.items()
            if did in device_entities
        }

        self._unavailable_devices = sorted(
            device_names.get(did, did)
            for did, since in self._unavailable_since.items()
            if (current_time - since) >= self._timeout.total_seconds()
        )
