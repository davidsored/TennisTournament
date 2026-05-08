# E2E Tests — Playwright

Tests end-to-end que abren un navegador real, navegan la app de Reflex y validan los flujos críticos desde la perspectiva del usuario.

## Estructura

```
tests/e2e/
├── conftest.py              ← BASE_URL, viewport, timeouts
├── pages/                   ← Page Object Model
│   ├── base_page.py
│   ├── home_page.py
│   ├── config_page.py
│   ├── league_page.py
│   ├── tournament_page.py
│   └── scoreboard_page.py
└── specs/                   ← Tests
    ├── test_league_flow.py        ← Flow A: ciclo de vida de liga
    ├── test_tournament_flow.py    ← Flow B: torneo + avance ganador
    └── test_config_persistence.py ← Flow C: tema persiste navegando
```

## Setup (una sola vez)

```bash
# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Instalar binarios de navegador (Chromium, Firefox, WebKit)
playwright install

# Solo Chromium (suficiente para CI)
playwright install chromium
```

## Levantar la app antes de los tests

```bash
# En una terminal aparte:
reflex run

# La app debe estar accesible en http://localhost:3000 (frontend)
# y http://localhost:8000 (backend WS).
```

> ⚠️ **Aislamiento:** Los tests escriben datos reales. Apunta el backend a una BD efímera (SQLite local con `DATABASE_URL=sqlite:///e2e.db` o un proyecto Supabase de staging). Nunca ejecutar contra producción.

## Ejecutar los tests

```bash
# Modo headless (rápido, sin ventana)
pytest tests/e2e -v

# Modo headed (ves el navegador en acción) — útil para depurar
pytest tests/e2e -v --headed

# Slow-mo: ralentiza cada acción 250ms (mejor para depurar fallos)
pytest tests/e2e -v --headed --slowmo 250

# Solo Flow B (torneo + avance del ganador)
pytest tests/e2e/specs/test_tournament_flow.py -v --headed

# Con tracing (graba video + HAR + screenshots para post-mortem)
pytest tests/e2e -v --tracing on
# Resultado en test-results/<test>/trace.zip → abrir con:
playwright show-trace test-results/<test>/trace.zip
```

## Variables de entorno

| Variable        | Default                     | Uso                                  |
| --------------- | --------------------------- | ------------------------------------ |
| `E2E_BASE_URL`  | `http://localhost:3000`     | Cambiar el target (CI / staging)     |

```bash
E2E_BASE_URL=https://staging.courtmanager.app pytest tests/e2e
```

## Patrón Page Object Model

Cada página de la app tiene su clase. Los specs **nunca** usan `page.locator()`:

```python
# ❌ NO en specs:
page.locator(".bg-primary > button").nth(2).click()

# ✅ SÍ en specs:
home = HomePage(page, base_url).goto()
home.click_create_league()
```

Los locators son **user-centric**:
- `get_by_role("button", name="Guardar Configuración")`
- `get_by_placeholder("Nombre del jugador")`
- `get_by_text("Crear Liga")`

## Flujos validados

| Flow | Spec                          | Qué valida                                    |
| ---- | ----------------------------- | --------------------------------------------- |
| A    | `test_league_flow.py`         | Crear liga, standings con N jugadores a 0 pts |
| B    | `test_tournament_flow.py`     | Ganar partido → ganador avanza al bracket     |
| C    | `test_config_persistence.py`  | Cambio de tema persiste entre rutas           |

## Troubleshooting

### Error: `playwright._impl._errors.TargetClosedError`
La app no está corriendo. Lanza `reflex run` en otra terminal.

### Error: `Locator.click: Timeout 15000ms exceeded`
El selector no encontró el elemento. Pasos:
1. Lanza con `--headed --slowmo 500` para ver dónde falla.
2. Inspecciona el DOM en DevTools y ajusta el locator en el Page Object.
3. Verifica que el texto/placeholder/aria-label coinciden con la app real (los selectores usados en POM se basan en `tournament_config.py`, `home.py`, etc.).

### Tests inestables (flaky)
Reflex hidrata por WebSocket; tras `goto()` esperamos `networkidle` pero a veces no es suficiente. Ajusta el `wait_for_hydration()` en `BasePage` si tu entorno es lento.

### Aislamiento de datos
Cada test crea sus propias entidades (liga, torneo) con nombres E2E reconocibles. Para limpiar entre runs:

```bash
# Borra la BD SQLite local
rm reflex.db
```

O para Postgres staging, ejecuta:
```sql
DELETE FROM league_matches WHERE 1=1;
DELETE FROM leagues WHERE name LIKE 'E2E %';
DELETE FROM tournaments WHERE name LIKE 'E2E %' OR name = 'Semis';
```
