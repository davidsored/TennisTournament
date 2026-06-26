# Changelog

Todos los cambios destacables de este proyecto se documentarán aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

—

## [0.2.0] - 2026-06-23

### Added

- **Feature "Partido Amistoso"**: nueva ruta `/casual-match` con formulario rápido (dos jugadores + formato) que arranca un partido sin necesidad de crear liga ni torneo.
  - `TennisTournament/states/casual_match_state.py` (`CasualMatchState`): inputs, steppers de sets (impares 1–9) y juegos (1–12), validación y emisión de `rx.redirect(...)` a `/scoreboard?casual=1&p1=…&p2=…&sets=…&games=…`.
  - `TennisTournament/pages/casual_match.py`: UI alineada con el sistema de diseño "Advantage" (top bar, cards, steppers, botón "Comenzar Partido").
  - Bento card "Partido Amistoso" en el Home y registro de la ruta en `TennisTournament.py`.
- **Hidratación URL del marcador** (`ScoreboardState.setup_scoreboard`): detecta `?casual=1` y carga los jugadores/config desde los query params; los refrescos del navegador preservan el progreso si los parámetros coinciden con el partido en curso.
- **Soporte Docker para desarrollo**:
  - `Dockerfile` (Python 3.12.3-slim + Node.js 20 + dependencias del sistema) con `reflex init` pre-cacheado.
  - `docker-compose.yml` con hot-reload, volumen nombrado `reflex_web`, `DATABASE_URL` por defecto a SQLite local y `WATCHFILES_FORCE_POLLING` para Docker Desktop en Windows/macOS.
  - `.dockerignore` para mantener la imagen ligera.
- **CI en GitHub Actions**:
  - `.github/workflows/ci.yml`: unit + integration sobre Python 3.12.3 en cada `push` y `pull_request` a `master`.
  - `.github/workflows/e2e.yml`: Playwright nightly (cron diario + `workflow_dispatch`) que arranca Reflex, espera al frontend, ejecuta los 5 specs E2E y sube como artifact los `debug_*.png` cuando hay fallos.
- **Tests automatizados de la feature** (26 nuevos, 24 + 2):
  - `tests/integration/test_casual_integration.py` (24 tests): defaults, setters, steppers, validación y URL exacta generada por `start_match`.
  - `tests/e2e/specs/test_casual_match_spec.py` (2 tests): recorrido completo Home → formulario → marcador y comprobación de sumar puntos en modo casual.
  - `tests/e2e/pages/casual_page.py`: Page Object reutilizando el patrón POM del proyecto.

### Changed

- **Home**: el bento grid pasa de `md:grid-cols-2` a `md:grid-cols-3` para acomodar la nueva tarjeta "Partido Amistoso".
- **README.md**:
  - Bloque "🆕 Novedades" en cabecera enlazando este CHANGELOG.
  - Badge **E2E** añadido y contador de tests actualizado (138 → 165).
  - Tabla "Funcionalidades clave" incluye Partido Amistoso.
  - Pirámide de testing recontada (107 unit / 53 integration / 5 E2E) y bloques de Integration/E2E mencionan los nuevos tests.
  - Estructura del proyecto refleja los nuevos archivos.
- **Tests pre-existentes**: 0 regresiones. Total: **165 passed** (107 + 53 + 5).

### Notas internas

#### Cómo publicar esta versión

Una vez mergeados los cambios en `master`:

```bash
# Tag + Release con notas auto-extraídas de este CHANGELOG
gh release create v0.2.0 \
  --title "v0.2.0 — Partido Amistoso, Docker y CI" \
  --notes-file <(awk '/^## \[0.2.0\]/,/^## \[/{if(/^## \[/ && !/0.2.0/)exit; print}' CHANGELOG.md)
```

Tras crear la release:

1. Generar y commitear las capturas pendientes (`assets/screenshots/casual_form.png`, `casual_scoreboard.png`, `home.png` re-capturado con 3 columnas).
2. En GitHub → "About" del repo: actualizar descripción y añadir Topics relevantes (`reflex`, `tennis`, `tailwindcss`, `python`, `docker`, `playwright`).

[Unreleased]: https://github.com/davidsored/TennisTournament/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/davidsored/TennisTournament/releases/tag/v0.2.0
