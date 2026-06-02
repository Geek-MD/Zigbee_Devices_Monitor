# Changelog

## 1.0.1

- Se corrige el `unique_id` del sensor para evitar entidades duplicadas al cambiar configuración.
- Se añade configuración opcional de frecuencia de revisión (`scan_interval`).
- Se agregan GitHub Actions (`ci.yaml` y `validate.yml`) y archivos base asociados (`requirements.txt`, `mypy.ini`, `hacs.json`).

## 1.0.0

- Se añade la integración `zigbee_devices_monitor` para Home Assistant.
- Se crea un sensor de tipo advertencia (`ok`/`warning`) para monitorizar entidades Zigbee no disponibles.
- Se añade configuración de tiempo de espera (`unavailable_timeout`), dominio Zigbee (`zigbee_domain`) y frecuencia de revisión (`scan_interval`).
