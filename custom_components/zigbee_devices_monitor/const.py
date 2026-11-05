"""Constants for Zigbee Devices Monitor."""

from __future__ import annotations

DOMAIN = "zigbee_devices_monitor"

DEFAULT_NAME = "Zigbee Devices Warning"
DEFAULT_UNAVAILABLE_TIMEOUT = 300
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_REDISCOVER_TRIES = 3
DEFAULT_REDISCOVER_DELAY = 0.1
DEFAULT_RECOVERY_TIMEOUT = 60
DEFAULT_DEVICE_DELAY = 5.0

CONF_UNAVAILABLE_TIMEOUT = "unavailable_timeout"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_EXCLUDED_DEVICES = "excluded_devices"
CONF_REDISCOVER_TRIES = "tries"
CONF_REDISCOVER_DELAY = "delay"
CONF_DEVICE_ID = "device_id"
CONF_RECOVERY_TIMEOUT = "recovery_timeout"
CONF_DEVICE_DELAY = "device_delay"

SERVICE_REDISCOVER_UNAVAILABLE = "rediscover_unavailable"
SERVICE_REINTERVIEW_DEVICE = "reinterview_device"

EVENT_DEVICE_ACTIVITY = f"{DOMAIN}_device_activity"
EVENT_DEVICE_RECOVERED = f"{DOMAIN}_device_recovered"
EVENT_DEVICE_RECOVERY_FAILED = f"{DOMAIN}_device_recovery_failed"

ZIGBEE_INTEGRATION_DOMAINS: list[str] = ["zha", "zigbee2mqtt"]
