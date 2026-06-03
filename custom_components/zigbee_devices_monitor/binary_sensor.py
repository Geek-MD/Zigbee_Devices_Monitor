"""Binary sensor platform for Zigbee Devices Monitor."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import inspect
import logging

import voluptuous as vol
import zigpy.types as t
from zigpy.exceptions import ControllerException, DeliveryError

from homeassistant.components import zha
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_REDISCOVER_DELAY,
    CONF_REDISCOVER_TRIES,
    CONF_SCAN_INTERVAL,
    CONF_UNAVAILABLE_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_REDISCOVER_DELAY,
    DEFAULT_REDISCOVER_TRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNAVAILABLE_TIMEOUT,
    DOMAIN,
    SERVICE_REDISCOVER_UNAVAILABLE,
    ZIGBEE_INTEGRATION_DOMAINS,
)

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.components.zha import helpers as zha_helpers
except ImportError:  # pragma: no cover
    zha_helpers = None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zigbee warning binary sensor from a config entry."""
    # Options are user-edited values and must override initial entry data.
    values = {**config_entry.data, **config_entry.options}
    async_add_entities(
        [
            ZigbeeWarningBinarySensor(
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

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_REDISCOVER_UNAVAILABLE,
        {
            vol.Optional(
                CONF_REDISCOVER_TRIES,
                default=DEFAULT_REDISCOVER_TRIES,
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Optional(
                CONF_REDISCOVER_DELAY,
                default=DEFAULT_REDISCOVER_DELAY,
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
        },
        "async_rediscover_unavailable",
    )


class ZigbeeWarningBinarySensor(BinarySensorEntity):
    """Monitor Zigbee devices and report unavailability warnings."""

    _attr_icon = "mdi:alert"
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

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
        self._unavailable_device_ids: list[str] = []
        self._unavailable_devices: list[str] = []
        self._unavailable_device_ieee: list[str] = []
        self._detected_integrations: list[str] = []
        self._cancel_interval: Callable[[], None] | None = None
        self._zha_ieee_by_device: dict[str, t.EUI64] = {}
        self._device_name_by_id: dict[str, str] = {}
        self._last_rediscovered_devices: list[str] = []
        self._last_rediscover_message: str | None = None

    @property
    def is_on(self) -> bool:
        """Return warning status."""
        return bool(self._unavailable_devices)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return details for unavailable devices."""
        return {
            "detected_integrations": self._detected_integrations,
            "timeout_seconds": self._timeout_seconds,
            "scan_interval": self._scan_interval,
            "unavailable_count": len(self._unavailable_devices),
            "unavailable_devices": self._unavailable_devices,
            "unavailable_device_ids": self._unavailable_device_ids,
            "unavailable_device_ieee": self._unavailable_device_ieee,
            "last_rediscovered_devices": self._last_rediscovered_devices,
            "last_rediscover_message": self._last_rediscover_message,
        }

    def _async_log_rediscover(self, message: str) -> None:
        """Write rediscover action details to Home Assistant logbook/history."""
        self._hass.bus.async_fire(
            "logbook_entry",
            {
                "name": self.name,
                "message": message,
                "entity_id": self.entity_id,
                "domain": DOMAIN,
            },
        )

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
    ) -> tuple[dict[str, str], dict[str, list[str]], dict[str, t.EUI64]]:
        """Return names/entities/ieee maps for all active Zigbee devices."""
        device_reg = dr.async_get(self._hass)
        entity_reg = er.async_get(self._hass)

        zigbee_entry_ids: set[str] = set()
        for entry in self._hass.config_entries.async_entries():
            if entry.domain in ZIGBEE_INTEGRATION_DOMAINS:
                zigbee_entry_ids.add(entry.entry_id)

        if not zigbee_entry_ids:
            return {}, {}, {}

        device_names: dict[str, str] = {}
        device_entities: dict[str, list[str]] = {}
        zha_ieee_by_device: dict[str, t.EUI64] = {}

        for device in device_reg.devices.values():
            if any(eid in zigbee_entry_ids for eid in device.config_entries):
                name = device.name_by_user or device.name or str(device.id)
                device_names[device.id] = name
                device_entities[device.id] = []
                for identifier_domain, identifier_value in device.identifiers:
                    if identifier_domain == "zha":
                        zha_ieee_by_device[device.id] = t.EUI64.convert(
                            str(identifier_value)
                        )

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
            {did: ieee for did, ieee in zha_ieee_by_device.items() if did in valid},
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
        device_names, device_entities, zha_ieee_by_device = self._get_zigbee_device_map()
        self._device_name_by_id = device_names
        self._zha_ieee_by_device = zha_ieee_by_device

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

        unavailable_device_ids = [
            did
            for did, since in self._unavailable_since.items()
            if (current_time - since) >= self._timeout.total_seconds()
        ]
        self._unavailable_device_ids = sorted(
            unavailable_device_ids,
            key=lambda did: device_names.get(did, did),
        )
        self._unavailable_devices = [
            device_names.get(did, did) for did in self._unavailable_device_ids
        ]
        self._unavailable_device_ieee = [
            # Non-ZHA devices (e.g. Zigbee2MQTT) are intentionally excluded.
            str(zha_ieee_by_device[did])
            for did in self._unavailable_device_ids
            if did in zha_ieee_by_device
        ]

    def _get_zha_gateway(self) -> object | None:
        """Return the active ZHA gateway object, if available."""
        if zha_helpers is not None and hasattr(zha_helpers, "get_zha_gateway"):
            return zha_helpers.get_zha_gateway(self._hass)
        # Fallback for Home Assistant versions where helper access is unavailable.
        return getattr(zha, "gateway", None)

    async def async_rediscover_unavailable(self, tries: int, delay: float) -> None:
        """Rediscover unavailable ZHA devices sequentially using handle_join."""
        self._process_states()

        if not self._unavailable_device_ids:
            return

        gateway = self._get_zha_gateway()
        if gateway is None or not hasattr(gateway, "application_controller"):
            raise ValueError(
                "ZHA integration is not loaded or gateway is unavailable. "
                "Ensure ZHA is configured and running."
            )

        app = gateway.application_controller
        failures: list[str] = []
        rediscovered_devices: list[str] = []

        for device_id in self._unavailable_device_ids:
            ieee = self._zha_ieee_by_device.get(device_id)
            if ieee is None:
                continue
            device_name = self._device_name_by_id.get(device_id, device_id)

            device = app.get_device(ieee)
            if device is None:
                failures.append(f"{device_name} ({ieee}): device not found in ZHA")
                continue

            success = False
            for attempt in range(1, tries + 1):
                try:
                    # `None` keeps parent info unset, matching ZHA Toolkit handle_join.
                    result = app.handle_join(int(device.nwk), device.ieee, None)
                    if inspect.isawaitable(result):
                        await result
                    success = True
                    rediscovered_devices.append(device_name)
                    self._async_log_rediscover(
                        f"Device rediscovered: {device_name} ({ieee})"
                    )
                    break
                except (
                    ControllerException,
                    DeliveryError,
                    TimeoutError,
                    ValueError,
                ) as err:
                    _LOGGER.debug(
                        "handle_join failed for %s (attempt %s/%s): %s",
                        ieee,
                        attempt,
                        tries,
                        err,
                    )
                    if attempt < tries:
                        await asyncio.sleep(delay)

            if not success:
                failures.append(f"{device_name} ({ieee}): failed after {tries} tries")

        self._last_rediscovered_devices = rediscovered_devices
        if rediscovered_devices:
            self._last_rediscover_message = ", ".join(rediscovered_devices)
        elif not failures:
            self._last_rediscover_message = "No ZHA devices were rediscovered."
        else:
            self._last_rediscover_message = None
        self.async_write_ha_state()

        if failures:
            raise ValueError("; ".join(failures))
