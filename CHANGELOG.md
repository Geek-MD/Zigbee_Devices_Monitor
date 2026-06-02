# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] - 2026-06-02

### Added
- Initial release of **Zigbee Devices Monitor**.
- UI config flow (`config_flow`) for first-time setup.
- Options flow support to reconfigure the integration from Home Assistant UI.
- Warning sensor with `ok`/`warning` states to monitor Zigbee availability.
- Configurable `name`, `zigbee_domain`, `unavailable_timeout`, and `scan_interval`.
- CI workflows (`ci.yaml`, `validate.yml`) with Ruff, mypy, and validation checks.
