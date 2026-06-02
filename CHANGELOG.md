# Changelog

## 0.1.0

- Primera versión de la integración.
- Se añade configuración inicial desde la UI mediante `config_flow`.
- Se añade reconfiguración desde la UI mediante opciones de la integración.
- Se agregan GitHub Actions (`ci.yaml` y `validate.yml`) y archivos base asociados (`requirements.txt`, `mypy.ini`, `hacs.json`).
- Se crea un sensor de tipo advertencia (`ok`/`warning`) para monitorizar entidades Zigbee no disponibles.
- Se añade configuración de tiempo de espera (`unavailable_timeout`), dominio Zigbee (`zigbee_domain`) y frecuencia de revisión (`scan_interval`).
