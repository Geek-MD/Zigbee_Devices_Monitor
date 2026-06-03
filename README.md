[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Zigbee_Devices_Monitor?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)
[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml/badge.svg)](https://github.com/Geek-MD/Zigbee_Devices_Monitor/actions/workflows/ci.yaml)

<p align="center">
  <img src="https://github.com/Geek-MD/Zigbee_Devices_Monitor/blob/main/custom_components/zigbee_devices_monitor/brand/icon.png?raw=true" width="180" alt="Zigbee Devices Monitor icon" />
</p>

# Zigbee Devices Monitor

Monitoriza disponibilidad de dispositivos Zigbee en Home Assistant y expone un único `binary_sensor` de alerta.

## ✨ Características

- Detección automática de integraciones Zigbee instaladas (`zha` y/o `zigbee2mqtt`).
- Monitorización a nivel **dispositivo** (no por entidad individual).
- Entidad `binary_sensor` con `device_class: problem` (`off` / `on`).
- Atributos con listado de dispositivos no disponibles e identificadores útiles para automatizaciones.
- Acción `zigbee_devices_monitor.rediscover_unavailable` para redescubrir dispositivos ZHA no disponibles.
- Registro en historial/logbook de cada dispositivo redescubierto.

## 📋 Requisitos

| Requisito | Versión mínima |
|-----------|----------------|
| Home Assistant | 2024.1.0 |
| HACS (opcional) | 1.6.0 |

## 📦 Instalación

### Opción 1: HACS (recomendada)

1. Ve a **HACS → Integrations**.
2. Abre el menú de tres puntos → **Custom repositories**.
3. Añade `https://github.com/Geek-MD/Zigbee_Devices_Monitor` como categoría **Integration**.
4. Busca **Zigbee Devices Monitor** e instálala.
5. Reinicia Home Assistant.

### Opción 2: Manual

1. Copia `custom_components/zigbee_devices_monitor` en `<config>/custom_components/`.
2. Reinicia Home Assistant.
3. Ve a **Settings → Devices & Services → Add Integration**.
4. Busca **Zigbee Devices Monitor**.

## ⚙️ Configuración

La integración se configura completamente desde UI.

| Opción | Descripción | Default |
|--------|-------------|---------|
| `name` | Nombre de la entidad de alerta | `Zigbee Devices Warning` |
| `unavailable_timeout` | Segundos que un dispositivo debe estar offline para alertar | `300` |
| `scan_interval` | Segundos entre escaneos | `30` |

Para reconfigurarla más adelante: **Settings → Devices & Services → Zigbee Devices Monitor → Configure**.

## 🧠 Entidad creada

La integración crea una entidad `binary_sensor` con:

- Estados: `off` / `on`
- Atributos:
  - `detected_integrations`
  - `timeout_seconds`
  - `scan_interval`
  - `unavailable_count`
  - `unavailable_devices`
  - `unavailable_device_ids`
  - `unavailable_device_ieee`
  - `last_rediscovered_devices`
  - `last_rediscover_message`

## 🔄 Acción: `rediscover_unavailable`

La acción de entidad `zigbee_devices_monitor.rediscover_unavailable`:

- Procesa dispositivos no disponibles de forma secuencial.
- Permite configurar:
  - `tries` (default: `3`)
  - `delay` (default: `0.1`)
- Registra en historial/logbook qué dispositivo se redescubrió.
- Actualiza atributos de la entidad para facilitar trazas en automatizaciones.

## 🗂️ Changelog

Consulta [CHANGELOG.md](CHANGELOG.md).

## 🛟 Soporte

Si encuentras un problema o quieres proponer una mejora, abre un issue en:
<https://github.com/Geek-MD/Zigbee_Devices_Monitor/issues>

## 📄 Licencia

Este proyecto está licenciado bajo [MIT](LICENSE).
