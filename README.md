# Zigbee_Devices_Monitor

Integración de Home Assistant que crea un sensor de advertencia para monitorizar la disponibilidad de dispositivos Zigbee.

## Instalación

1. Copia la carpeta `custom_components/zigbee_devices_monitor` en tu instalación de Home Assistant.
2. Reinicia Home Assistant.

## Configuración (`configuration.yaml`)

```yaml
sensor:
  - platform: zigbee_devices_monitor
    name: Zigbee Devices Warning
    zigbee_domain: zha
    unavailable_timeout: 300
```

### Opciones

- `name`: nombre del sensor.
- `zigbee_domain`: dominio de la integración Zigbee a monitorizar (por defecto: `zha`).
- `unavailable_timeout`: segundos de espera antes de marcar un dispositivo como no disponible (por defecto: `300`).

## Comportamiento del sensor

- Estado `ok`: no hay dispositivos Zigbee no disponibles durante el período configurado.
- Estado `warning`: hay uno o más dispositivos no disponibles durante el período configurado.
- Atributo `unavailable_devices`: lista de entidades Zigbee no disponibles tras superar el tiempo configurado.
