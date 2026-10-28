# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

## [0.2.0] - 2026-10-28
### Cambiado
- axe-core 4.10.2 viene incluido en el paquete: ya no se necesita Node ni `npm install`.
- Instalación con `pip install -e ".[dev]"` y comando `a11y-audit` (sin `PYTHONPATH`).
- Cada página se escanea en una pestaña nueva para no arrastrar cookies ni popups.

### Agregado
- Sección `settings` en el YAML: `timeout_ms`, `delay_s` y `min_score`.
- Códigos de salida 0/1/2 para usar la herramienta como filtro en CI.
- Pausa entre páginas y user-agent identificable.
- Validación de configuración con mensajes claros.
- Pruebas de configuración, reportes, CLI y accesibilidad del propio reporte (28 en total).
- CI en Ubuntu y Windows, linter ruff y Dependabot.

## [0.1.0] - 2026-10-28
### Agregado
- Primera versión: escaneo EN/ES, verificación de `lang`, puntaje y reportes HTML, JSON y CSV.
