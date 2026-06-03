"""Constants for Zigbee Devices Monitor."""

from __future__ import annotations

DOMAIN = "zigbee_devices_monitor"

DEFAULT_NAME = "Zigbee Devices Warning"
DEFAULT_UNAVAILABLE_TIMEOUT = 300
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_REDISCOVER_TRIES = 3
DEFAULT_REDISCOVER_DELAY = 0.1

CONF_UNAVAILABLE_TIMEOUT = "unavailable_timeout"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_REDISCOVER_TRIES = "tries"
CONF_REDISCOVER_DELAY = "delay"

SERVICE_REDISCOVER_UNAVAILABLE = "rediscover_unavailable"

ZIGBEE_INTEGRATION_DOMAINS: list[str] = ["zha", "zigbee2mqtt"]
