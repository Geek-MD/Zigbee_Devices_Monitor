"""Binary sensor platform for Zigbee Devices Monitor."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

import probatio
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
    CONF_DEVICE_DELAY,
    CONF_DEVICE_ID,
    CONF_EXCLUDED_DEVICES,
    CONF_RECOVERY_TIMEOUT,
    CONF_REDISCOVER_DELAY,
    CONF_REDISCOVER_TRIES,
    CONF_SCAN_INTERVAL,
    CONF_UNAVAILABLE_TIMEOUT,
    DEFAULT_DEVICE_DELAY,
    DEFAULT_NAME,
    DEFAULT_RECOVERY_TIMEOUT,
    DEFAULT_REDISCOVER_DELAY,
    DEFAULT_REDISCOVER_TRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNAVAILABLE_TIMEOUT,
    DOMAIN,
    EVENT_DEVICE_ACTIVITY,
    EVENT_DEVICE_RECOVERED,
    EVENT_DEVICE_RECOVERY_FAILED,
    SERVICE_REDISCOVER_UNAVAILABLE,
    SERVICE_REINTERVIEW_DEVICE,
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
                scan_interval=int(
                    values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ),
                excluded_device_ids=list(values.get(CONF_EXCLUDED_DEVICES, [])),
            )
        ],
        True,
    )

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_REDISCOVER_UNAVAILABLE,
        {
            probatio.Optional(
                CONF_REDISCOVER_TRIES,
                default=DEFAULT_REDISCOVER_TRIES,
            ): probatio.All(probatio.Coerce(int), probatio.Range(min=1)),
            probatio.Optional(
                CONF_REDISCOVER_DELAY,
                default=DEFAULT_REDISCOVER_DELAY,
            ): probatio.All(probatio.Coerce(float), probatio.Range(min=0)),
            probatio.Optional(
                CONF_RECOVERY_TIMEOUT,
                default=DEFAULT_RECOVERY_TIMEOUT,
            ): probatio.All(probatio.Coerce(int), probatio.Range(min=1)),
            probatio.Optional(
                CONF_DEVICE_DELAY,
                default=DEFAULT_DEVICE_DELAY,
            ): probatio.All(probatio.Coerce(float), probatio.Range(min=0)),
        },
        "async_rediscover_unavailable",
    )
    platform.async_register_entity_service(
        SERVICE_REINTERVIEW_DEVICE,
        {
            probatio.Required(CONF_DEVICE_ID): str,
            probatio.Optional(
                CONF_REDISCOVER_TRIES,
                default=DEFAULT_REDISCOVER_TRIES,
            ): probatio.All(probatio.Coerce(int), probatio.Range(min=1)),
            probatio.Optional(
                CONF_REDISCOVER_DELAY,
                default=DEFAULT_REDISCOVER_DELAY,
            ): probatio.All(probatio.Coerce(float), probatio.Range(min=0)),
            probatio.Optional(
                CONF_RECOVERY_TIMEOUT,
                default=DEFAULT_RECOVERY_TIMEOUT,
            ): probatio.All(probatio.Coerce(int), probatio.Range(min=1)),
        },
        "async_reinterview_device",
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
        excluded_device_ids: list[str] | None = None,
    ) -> None:
        self._hass = hass
        self._attr_name = name
        self._attr_unique_id = "zigbee_devices_monitor_warning"
        self._timeout = timedelta(seconds=unavailable_timeout)
        self._timeout_seconds = unavailable_timeout
        self._scan_interval = scan_interval
        self._excluded_device_ids: list[str] = excluded_device_ids or []
        self._unavailable_since: dict[str, float] = {}
        self._unavailable_device_ids: list[str] = []
        self._unavailable_devices: list[str] = []
        self._unavailable_device_ieee: list[str] = []
        self._detected_integrations: list[str] = []
        self._cancel_interval: Callable[[], None] | None = None
        self._zha_ieee_by_device: dict[str, t.EUI64] = {}
        self._device_name_by_id: dict[str, str] = {}
        self._last_seen_by_device: dict[str, float] = {}
        self._activity_event_fired: set[str] = set()
        self._unavailable_since_iso: dict[str, str] = {}
        self._last_rediscover_failures: list[str] = []
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
            "excluded_device_ids": self._excluded_device_ids,
            "unavailable_count": len(self._unavailable_devices),
            "unavailable_devices": self._unavailable_devices,
            "unavailable_device_ids": self._unavailable_device_ids,
            "unavailable_device_ieee": self._unavailable_device_ieee,
            "last_rediscover_failures": self._last_rediscover_failures,
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

    def _async_fire_device_event(
        self,
        event_type: str,
        device_id: str,
        ieee: t.EUI64,
        entity_ids: list[str],
        **extra: object,
    ) -> None:
        """Fire a device activity or recovery event."""
        self._hass.bus.async_fire(
            event_type,
            {
                "device_id": device_id,
                "device_name": self._device_name_by_id.get(device_id, device_id),
                "ieee": str(ieee),
                "entity_ids": entity_ids,
                **extra,
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
            if (
                entry.domain in ZIGBEE_INTEGRATION_DOMAINS
                and entry.domain not in detected
            ):
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

        for device in device_reg.devices:
            if device.config_entry_id in zigbee_entry_ids:
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

    def _get_zha_last_seen(self, ieee: t.EUI64) -> float | None:
        """Return zigpy's last-seen timestamp for a ZHA device."""
        gateway = self._get_zha_gateway()
        if gateway is None or not hasattr(gateway, "application_controller"):
            return None
        try:
            device = gateway.application_controller.get_device(ieee=ieee)
        except KeyError:
            return None
        last_seen = getattr(device, "last_seen", None)
        return float(last_seen) if last_seen is not None else None

    def _async_detect_device_activity(
        self,
        previously_unavailable: set[str],
        device_entities: dict[str, list[str]],
        zha_ieee_by_device: dict[str, t.EUI64],
    ) -> None:
        """Fire once when an unavailable ZHA device reports new activity."""
        active_device_ids = set(zha_ieee_by_device)
        self._last_seen_by_device = {
            device_id: last_seen
            for device_id, last_seen in self._last_seen_by_device.items()
            if device_id in active_device_ids
        }

        for device_id, ieee in zha_ieee_by_device.items():
            last_seen = self._get_zha_last_seen(ieee)
            previous_last_seen = self._last_seen_by_device.get(device_id)
            if last_seen is not None:
                self._last_seen_by_device[device_id] = last_seen

            if (
                device_id not in previously_unavailable
                or device_id in self._activity_event_fired
                or last_seen is None
                or previous_last_seen is None
                or last_seen <= previous_last_seen
            ):
                continue

            self._activity_event_fired.add(device_id)
            self._async_fire_device_event(
                EVENT_DEVICE_ACTIVITY,
                device_id,
                ieee,
                device_entities.get(device_id, []),
                last_seen=datetime.fromtimestamp(last_seen, UTC).isoformat(),
                unavailable_since=self._unavailable_since_iso.get(device_id),
            )

    def _process_states(self) -> None:
        """Update offline devices list based on timeout."""
        current_time = self._hass.loop.time()
        previously_unavailable = set(self._unavailable_device_ids)
        self._detected_integrations = self._detect_integrations()
        device_names, device_entities, zha_ieee_by_device = (
            self._get_zigbee_device_map()
        )
        self._device_name_by_id = device_names
        self._zha_ieee_by_device = zha_ieee_by_device

        self._async_detect_device_activity(
            previously_unavailable,
            device_entities,
            zha_ieee_by_device,
        )

        for device_id, entity_ids in device_entities.items():
            if device_id in self._excluded_device_ids:
                self._unavailable_since.pop(device_id, None)
                self._unavailable_since_iso.pop(device_id, None)
                continue
            if self._is_device_offline(entity_ids):
                if device_id not in self._unavailable_since:
                    self._unavailable_since[device_id] = current_time
                    self._unavailable_since_iso[device_id] = datetime.now(
                        UTC
                    ).isoformat()
            else:
                self._unavailable_since.pop(device_id, None)
                self._unavailable_since_iso.pop(device_id, None)

        # Remove stale entries for devices no longer in the registry
        self._unavailable_since = {
            did: since
            for did, since in self._unavailable_since.items()
            if did in device_entities
        }
        self._unavailable_since_iso = {
            did: since
            for did, since in self._unavailable_since_iso.items()
            if did in self._unavailable_since
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
        self._activity_event_fired.intersection_update(self._unavailable_device_ids)

    def _get_zha_gateway(self) -> Any | None:
        """Return the active ZHA gateway object, if available."""
        if zha_helpers is not None and hasattr(zha_helpers, "get_zha_gateway"):
            return zha_helpers.get_zha_gateway(self._hass)
        # Fallback for Home Assistant versions where helper access is unavailable.
        return getattr(zha, "gateway", None)

    def _require_zha_gateway(self) -> Any:
        """Return a ZHA gateway that supports full device re-interviews."""
        gateway = self._get_zha_gateway()
        if gateway is None or not hasattr(gateway, "async_reinterview_device"):
            raise ValueError(
                "ZHA integration is not loaded or gateway is unavailable. "
                "Ensure ZHA is configured and running."
            )
        return gateway

    def _has_available_entity(self, device_id: str) -> bool:
        """Return True when at least one enabled device entity is available."""
        _, device_entities, _ = self._get_zigbee_device_map()
        return any(
            (state := self._hass.states.get(entity_id)) is not None
            and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
            for entity_id in device_entities.get(device_id, [])
        )

    async def _async_wait_until_device_available(
        self, device_id: str, timeout: int
    ) -> bool:
        """Wait until at least one enabled entity becomes available."""
        deadline = self._hass.loop.time() + timeout
        while self._hass.loop.time() < deadline:
            if self._has_available_entity(device_id):
                return True
            await asyncio.sleep(1)
        return self._has_available_entity(device_id)

    async def _async_recover_device(
        self,
        device_id: str,
        tries: int,
        delay: float,
        recovery_timeout: int,
    ) -> tuple[bool, str]:
        """Re-interview one ZHA device and verify entity recovery."""
        device_names, device_entities, zha_ieee_by_device = (
            self._get_zigbee_device_map()
        )
        self._device_name_by_id = device_names
        self._zha_ieee_by_device = zha_ieee_by_device

        ieee = zha_ieee_by_device.get(device_id)
        if ieee is None:
            return False, f"{device_id}: device is not an active ZHA device"

        gateway = self._require_zha_gateway()
        device_name = device_names.get(device_id, device_id)
        last_error: Exception | None = None

        for attempt in range(1, tries + 1):
            try:
                async with asyncio.timeout(recovery_timeout):
                    await gateway.async_reinterview_device(ieee)
                if await self._async_wait_until_device_available(
                    device_id, recovery_timeout
                ):
                    entity_ids = self._get_zigbee_device_map()[1].get(device_id, [])
                    self._async_log_rediscover(
                        f"Device recovered: {device_name} ({ieee})"
                    )
                    self._async_fire_device_event(
                        EVENT_DEVICE_RECOVERED,
                        device_id,
                        ieee,
                        entity_ids,
                        attempt=attempt,
                    )
                    return True, device_name
            except (
                ControllerException,
                DeliveryError,
                TimeoutError,
                ValueError,
            ) as err:
                last_error = err
                _LOGGER.debug(
                    "ZHA re-interview failed for %s (attempt %s/%s): %s",
                    ieee,
                    attempt,
                    tries,
                    err,
                )

            if attempt < tries:
                await asyncio.sleep(delay)

        entity_ids = self._get_zigbee_device_map()[1].get(device_id, [])
        reason = (
            str(last_error)
            if last_error is not None
            else "entities remained unavailable after the re-interview"
        )
        self._async_fire_device_event(
            EVENT_DEVICE_RECOVERY_FAILED,
            device_id,
            ieee,
            entity_ids,
            attempts=tries,
            reason=reason,
        )
        return False, f"{device_name} ({ieee}): {reason}"

    async def async_reinterview_device(
        self,
        device_id: str,
        tries: int,
        delay: float,
        recovery_timeout: int,
    ) -> None:
        """Re-interview one explicitly selected ZHA device."""
        success, result = await self._async_recover_device(
            device_id,
            tries,
            delay,
            recovery_timeout,
        )
        self._last_rediscover_failures = [] if success else [result]
        self._last_rediscovered_devices = [result] if success else []
        self._last_rediscover_message = result if success else None
        self._process_states()
        self.async_write_ha_state()
        if not success:
            _LOGGER.warning("ZHA device recovery failed: %s", result)

    async def async_rediscover_unavailable(
        self,
        tries: int,
        delay: float,
        recovery_timeout: int,
        device_delay: float,
    ) -> None:
        """Re-interview unavailable ZHA devices without raising for offline devices."""
        self._last_rediscovered_devices = []
        self._last_rediscover_failures = []
        self._last_rediscover_message = None
        self._process_states()

        unavailable_device_ids = [
            device_id
            for device_id in self._unavailable_device_ids
            if device_id in self._zha_ieee_by_device
        ]
        if not unavailable_device_ids:
            self.async_write_ha_state()
            return

        failures: list[str] = []
        rediscovered_devices: list[str] = []

        for index, device_id in enumerate(unavailable_device_ids):
            success, result = await self._async_recover_device(
                device_id,
                tries,
                delay,
                recovery_timeout,
            )
            if success:
                rediscovered_devices.append(result)
            else:
                failures.append(result)
            if index < len(unavailable_device_ids) - 1 and device_delay > 0:
                await asyncio.sleep(device_delay)

        self._last_rediscover_failures = failures
        self._last_rediscovered_devices = rediscovered_devices
        if rediscovered_devices:
            self._last_rediscover_message = ", ".join(rediscovered_devices)
        elif not failures:
            self._last_rediscover_message = "No ZHA devices were recovered."
        else:
            self._last_rediscover_message = None
        self._process_states()
        self.async_write_ha_state()

        if failures:
            _LOGGER.warning("ZHA device recovery failed: %s", "; ".join(failures))
