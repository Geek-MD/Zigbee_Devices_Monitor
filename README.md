[![Geek-MD - Zigbee Devices Monitor](https://img.shields.io/static/v1?label=Geek-MD&message=Zigbee%20Devices%20Monitor&color=blue&logo=github)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Stars](https://img.shields.io/github/stars/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)
[![Forks](https://img.shields.io/github/forks/Geek-MD/Zigbee_Devices_Monitor?style=social)](https://github.com/Geek-MD/Zigbee_Devices_Monitor)

[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Zigbee_Devices_Monitor?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)

<!-- ha-marketplace:exclude-start -->
[![Open your Home Assistant instance and open Zigbee Devices Monitor in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=Geek-MD&repository=Zigbee_Devices_Monitor&category=integration)
<!-- ha-marketplace:exclude-end -->

[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml/badge.svg)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<img src="https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/custom_components/zigbee_devices_monitor/brand/icon.png?raw=true" width="180" alt="Zigbee Devices Monitor icon" />

# Zigbee Devices Monitor

A Home Assistant custom integration that monitors Zigbee device availability and exposes a single warning `binary_sensor`.

## v0.4.1 update

Adds the Home Assistant 2026.11 Marketplace wireless-protocol classification. It includes the activity-aware recovery introduced in v0.4.0: the integration can detect when a previously unavailable ZHA device communicates again, emit an automation event, perform a full ZHA re-interview, rebuild its entities, and verify recovery. Existing configuration is preserved.

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

## ✨ Features

- Automatically detects installed Zigbee integrations (`zha` and/or `zigbee2mqtt`).
- Monitors availability at the **device level** (not per-entity).
- Creates one `binary_sensor` with `device_class: problem` (`off` / `on`).
- Detects new ZHA activity through device `last_seen` updates and emits one event per unavailability episode.
- Provides targeted and bulk ZHA re-interview actions with recovery verification.
- Rebuilds endpoints, clusters, quirks, bindings, reporting, and entities through ZHA's native re-interview flow.
- Processes devices sequentially with a configurable pause between devices.
- Writes one history/logbook entry per successfully recovered device.
- Uses [Probatio](https://probatio.frenck.dev/) directly for configuration and entity action validation.

## 📋 Requirements

| Requirement | Minimum version |
|-------------|-----------------|
| Home Assistant | 2026.9.0 |
| HACS (optional) | 1.6.0 |

Home Assistant 2026.9 or newer is required because this release imports the
Probatio validation engine directly instead of using the legacy Voluptuous API.

## 🛠 Installation

### Option 1: Marketplace (Home Assistant 2026.11 or newer)

1. Go to **Settings → Marketplace**.
2. Search for **Zigbee Devices Monitor**, select **Install**, and confirm the version.
3. Complete setup when Home Assistant opens the integration page.

### Option 2: HACS (Home Assistant 2026.9–2026.10 only)

1. Open **HACS → Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/Geek-MD/Zigbee_Devices_Monitor` as **Integration**.
4. Search for **Zigbee Devices Monitor** and install.
5. Restart Home Assistant.

### Option 3: Manual installation

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
| `excluded_devices` | Devices to exclude from monitoring | *(none)* |

To reconfigure later: **Settings → Devices & Services → Zigbee Devices Monitor → Configure**.

## 🧠 Created entity

The integration creates one `binary_sensor` with:

- States: `off` / `on`
- Attributes:
  - `detected_integrations`
  - `timeout_seconds`
  - `scan_interval`
  - `excluded_device_ids`
  - `unavailable_count`
  - `unavailable_devices`
  - `unavailable_device_ids`
  - `unavailable_device_ieee`
  - `last_rediscovered_devices`
  - `last_rediscover_message`

## 🔄 Recovery actions

### `rediscover_unavailable`

The entity action `zigbee_devices_monitor.rediscover_unavailable`:

- Must be called with the monitor entity as target (`binary_sensor.zigbee_devices_warning`, or your custom name).
- Fully re-interviews unavailable ZHA devices sequentially.
- Supports:
  - `tries` (default: `3`)
  - `delay` between attempts for the same device (default: `0.1` seconds)
  - `recovery_timeout` for the re-interview and entity verification (default: `60` seconds)
  - `device_delay` between different devices (default: `5` seconds)
- Recalculates unavailable devices internally at execution time (attributes are informative; they are not passed as manual input).
- Considers a device recovered only after at least one enabled entity is no longer `unavailable` or `unknown`.
- Records each successful recovery in Home Assistant history/logbook.
- Updates entity attributes to improve visibility in automation traces.

### `reinterview_device`

The targeted entity action `zigbee_devices_monitor.reinterview_device`:

- Must be called with the monitor entity as target.
- Requires a ZHA `device_id`.
- Can process the device even if recent activity already removed it from the unavailable list.
- Supports `tries`, `delay`, and `recovery_timeout` with the same defaults as the bulk action.
- Emits a recovery result event after verification.

## 📡 Events

### `zigbee_devices_monitor_device_activity`

Fires once per unavailability episode when the monitor sees a newer ZHA `last_seen` timestamp for a device that was already reported as unavailable.

Event data:

| Field | Description |
|-------|-------------|
| `device_id` | Home Assistant device registry ID |
| `device_name` | Human-readable device name |
| `ieee` | ZHA IEEE address |
| `entity_ids` | Enabled entities associated with the device |
| `last_seen` | Timestamp of the newly detected activity |
| `unavailable_since` | Timestamp when the offline episode started |

### Recovery result events

- `zigbee_devices_monitor_device_recovered` fires after a successful re-interview and entity recovery. It includes `attempt`.
- `zigbee_devices_monitor_device_recovery_failed` fires after all attempts fail. It includes `attempts` and `reason`.

Activity detection does not make an unreachable device respond. Battery-powered devices must wake and communicate naturally before the activity event can fire.

## 🤖 Automation examples

### 1) Notify when unavailable devices are detected

```yaml
alias: Zigbee warning notification
description: Send a mobile notification when the warning sensor turns on.
triggers:
  - trigger: state
    entity_id: binary_sensor.zigbee_devices_warning
    to: "on"
actions:
  - action: notify.mobile_app_your_phone
    data:
      title: Zigbee Devices Monitor
      message: >
        {{ state_attr('binary_sensor.zigbee_devices_warning', 'unavailable_count') }}
        device(s) unavailable:
        {{ state_attr('binary_sensor.zigbee_devices_warning', 'unavailable_devices') }}
mode: single
```

### 2) Auto-run rediscovery when warning turns on

```yaml
alias: Zigbee auto rediscover
description: Run rediscovery with retries when unavailable devices are detected.
triggers:
  - trigger: state
    entity_id: binary_sensor.zigbee_devices_warning
    to: "on"
actions:
  - action: zigbee_devices_monitor.rediscover_unavailable
    target:
      entity_id: binary_sensor.zigbee_devices_warning
    data:
      tries: 3
      delay: 0.2
      recovery_timeout: 60
      device_delay: 5
mode: single
```

### 3) Re-interview a battery device when it wakes

```yaml
alias: Zigbee recover device on activity
description: Re-interview an unavailable ZHA device as soon as it communicates again.
triggers:
  - trigger: event
    event_type: zigbee_devices_monitor_device_activity
actions:
  - action: zigbee_devices_monitor.reinterview_device
    target:
      entity_id: binary_sensor.zigbee_devices_warning
    data:
      device_id: "{{ trigger.event.data.device_id }}"
      tries: 2
      delay: 1
      recovery_timeout: 60
mode: queued
max: 10
```

Using `queued` mode prevents simultaneous re-interviews when several devices report activity close together.

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
