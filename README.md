[![Geek-MD - Zigbee Devices Monitor](https://img.shields.io/static/v1?label=Geek-MD&message=Zigbee%20Devices%20Monitor&color=blue&logo=github)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Stars](https://img.shields.io/github/stars/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Forks](https://img.shields.io/github/forks/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)

[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Zigbee_Devices_Monitor?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)

[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml/badge.svg)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<img src="https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/custom_components/zigbee_devices_monitor/brand/icon.png?raw=true" width="180" alt="Zigbee Devices Monitor icon" />

# Zigbee Devices Monitor

A Home Assistant custom integration that monitors Zigbee device availability and exposes a single warning `binary_sensor`.

## ✨ Features

- Automatically detects installed Zigbee integrations (`zha` and/or `zigbee2mqtt`).
- Monitors availability at the **device level** (not per-entity).
- Creates one `binary_sensor` with `device_class: problem` (`off` / `on`).
- Exposes attributes with unavailable device details and rediscovery inputs.
- Provides the `zigbee_devices_monitor.rediscover_unavailable` action for unavailable ZHA devices.
- Writes one history/logbook entry per successfully rediscovered device.

## 📋 Requirements

| Requirement | Minimum version |
|-------------|-----------------|
| Home Assistant | 2024.1.0 |
| HACS (optional) | 1.6.0 |

## 📦 Installation

### Option 1: HACS (recommended)

1. Open **HACS → Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/Geek-MD/Zigbee_Devices_Monitor` as **Integration**.
4. Search for **Zigbee Devices Monitor** and install.
5. Restart Home Assistant.

### Option 2: Manual

1. Copy `custom_components/zigbee_devices_monitor` to `<config>/custom_components/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **Zigbee Devices Monitor**.

## ⚙️ Configuration

Configuration is fully UI-based.

| Option | Description | Default |
|--------|-------------|---------|
| `name` | Warning entity name | `Zigbee Devices Warning` |
| `unavailable_timeout` | Seconds a device must be offline before alerting | `300` |
| `scan_interval` | Seconds between scans | `30` |

To reconfigure later: **Settings → Devices & Services → Zigbee Devices Monitor → Configure**.

## 🧠 Created entity

The integration creates one `binary_sensor` with:

- States: `off` / `on`
- Attributes:
  - `detected_integrations`
  - `timeout_seconds`
  - `scan_interval`
  - `unavailable_count`
  - `unavailable_devices`
  - `unavailable_device_ids`
  - `unavailable_device_ieee`
  - `last_rediscovered_devices`
  - `last_rediscover_message`

## 🔄 Action: `rediscover_unavailable`

The entity action `zigbee_devices_monitor.rediscover_unavailable`:

- Processes unavailable devices sequentially.
- Supports:
  - `tries` (default: `3`)
  - `delay` (default: `0.1`)
- Records each successful rediscovery in Home Assistant history/logbook.
- Updates entity attributes to improve visibility in automation traces.

## 🗂️ Changelog

See [CHANGELOG.md](CHANGELOG.md).

## 🛟 Support

For issues or feature requests:
<https://github.com/Geek-MD/Zigbee_Devices_Monitor/issues>

## 📜 License

MIT License. See [LICENSE](https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/LICENSE) for details.

---

<div align="center">
  
💻 **Proudly developed with GitHub Copilot** 🚀

</div>
