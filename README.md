# Zigbee_Devices_Monitor

Integración de Home Assistant que crea un sensor de advertencia para monitorizar la disponibilidad de dispositivos Zigbee.

## Instalación

1. Copia la carpeta `custom_components/zigbee_devices_monitor` en tu instalación de Home Assistant.
2. Reinicia Home Assistant.

## Configuración desde la UI

1. Ve a **Ajustes → Dispositivos y servicios → Añadir integración**.
2. Busca **Zigbee Devices Monitor**.
3. Define los parámetros iniciales en el formulario de la integración.

### Reconfiguración desde la UI

1. Ve a **Ajustes → Dispositivos y servicios**.
2. Abre la integración **Zigbee Devices Monitor**.
3. Pulsa **Configurar** para ajustar los valores cuando quieras.

### Opciones

- `name`: nombre del sensor.
- `zigbee_domain`: dominio de la integración Zigbee a monitorizar (por defecto: `zha`).
- `unavailable_timeout`: segundos de espera antes de marcar un dispositivo como no disponible (por defecto: `300`).
- `scan_interval`: frecuencia en segundos para revisar el estado de las entidades (por defecto: `30`).

## Comportamiento del sensor

- Estado `ok`: no hay dispositivos Zigbee no disponibles durante el período configurado.
- Estado `warning`: hay uno o más dispositivos no disponibles durante el período configurado.
- Atributo `unavailable_devices`: lista de entidades Zigbee no disponibles tras superar el tiempo configurado.
