[![Geek-MD - Zigbee Devices Monitor](https://img.shields.io/static/v1?label=Geek-MD&message=Zigbee%20Devices%20Monitor&color=blue&logo=github)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Stars](https://img.shields.io/github/stars/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Forks](https://img.shields.io/github/forks/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)

[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Zigbee_Devices_Monitor?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)

[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml/badge.svg)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<img width="200" height="200" alt="image" src="https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/custom_components/zigbee_devices_monitor/brand/icon.png?raw=true" />

# Zigbee Devices Monitor

A custom Home Assistant integration that monitors entities from a Zigbee integration domain (for example `zha`) and exposes a single warning sensor.

## Features

- Creates one sensor that reports overall Zigbee availability status.
- Sensor states:
  - `ok`: no Zigbee entities have been unavailable longer than the configured timeout.
  - `warning`: one or more Zigbee entities have been unavailable longer than the configured timeout.
- Automatically scans entities linked to the configured Zigbee integration domain.
- Configurable entirely from the Home Assistant UI.
- Supports post-install reconfiguration through integration options.
- Manifest aligned with Home Assistant validation requirements (`iot_class`, `issue_tracker`).
- HACS-compatible.

## Requirements

| Requirement | Minimum version |
|-------------|------------------|
| Home Assistant | 2024.1.0 |
| HACS (optional) | 1.6.0 |

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/Geek-MD/Zigbee_Devices_Monitor` as category **Integration**.
4. Search for **Zigbee Devices Monitor** and install it.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/zigbee_devices_monitor` into `<config>/custom_components/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **Zigbee Devices Monitor**.

## Configuration

The integration is configured through the UI.

### Initial setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Zigbee Devices Monitor**.
3. Configure the options below and submit.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| Name (`name`) | Name of the warning sensor entity | `Zigbee Devices Warning` |
| Zigbee domain (`zigbee_domain`) | Integration domain to monitor (`zha`, `z2m`, etc.) | `zha` |
| Unavailable timeout (`unavailable_timeout`) | Seconds an entity must remain unavailable before alerting | `300` |
| Scan interval (`scan_interval`) | Seconds between availability scans | `30` |

### Reconfigure later

1. Go to **Settings → Devices & Services**.
2. Open **Zigbee Devices Monitor**.
3. Click **Configure**.

## Sensor details

The integration creates a sensor with the configured name.

### State

- `ok`
- `warning`

### Attributes

- `zigbee_domain`: monitored domain.
- `timeout_seconds`: timeout used to mark entities as unavailable.
- `scan_interval`: periodic check interval.
- `unavailable_count`: total entities currently in warning condition.
- `unavailable_devices`: list of affected entity IDs.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

This project is licensed under the [MIT License](LICENSE).

## Support

For issues or feature requests, use the [GitHub issue tracker](https://github.com/Geek-MD/Zigbee_Devices_Monitor/issues).

---

<div align="center">

💻 **Proudly developed with GitHub Copilot** 🚀

</div>
