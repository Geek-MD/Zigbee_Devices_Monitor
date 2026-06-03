# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.2] - 2026-06-03

### Changed
- Replaced manual `zigbee_domain` configuration with automatic detection of installed Zigbee integrations (ZHA and/or Zigbee2MQTT).
- Monitoring now operates at the **device level** instead of the entity level: a Zigbee device is considered offline when all of its non-disabled entities report `unavailable` or `unknown` state.
- The `unavailable_devices` sensor attribute now lists **device names** (human-readable) instead of raw entity IDs.
- The `zigbee_domain` attribute is replaced by `detected_integrations`, listing every Zigbee integration domain found in the current HA instance.

### Removed
- `zigbee_domain` configuration option (no longer needed — integration is auto-detected).

## [v0.1.1] - 2026-06-02

### Fixed
- Added `iot_class: local_polling` to `manifest.json` to satisfy Home Assistant manifest validation.
- Added `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` in `__init__.py` to satisfy Home Assistant config schema validation for integrations implementing `async_setup`.
- Added `issue_tracker` in `manifest.json` to improve manifest completeness for validation tools.

## [v0.1.0] - 2026-06-02

### Added
- Initial release of **Zigbee Devices Monitor**.
- UI config flow (`config_flow`) for first-time setup.
- Options flow support to reconfigure the integration from Home Assistant UI.
- Warning sensor with `ok`/`warning` states to monitor Zigbee availability.
- Configurable `name`, `zigbee_domain`, `unavailable_timeout`, and `scan_interval`.
- CI workflows (`ci.yaml`, `validate.yml`) with Ruff, mypy, and validation checks.
