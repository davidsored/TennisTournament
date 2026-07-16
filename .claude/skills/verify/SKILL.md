---
name: verify
description: Receta para arrancar y verificar CourtManager (Reflex) en local sin tocar Supabase — build, launch, flujos clave y gotchas de WSL.
---

# Verificar CourtManager (Reflex) en local

## Contexto del entorno
- El venv es de **WSL** (`.venv/bin/`, creado con /usr/bin/python3.12). Desde Windows, todo se ejecuta vía `wsl.exe -e bash -c "..."`.
- ⚠️ `.env` contiene el `DATABASE_URL` de **Supabase producción**. NUNCA arrancar sin exportar un `DATABASE_URL` local: `rxconfig.py` hace `load_dotenv()` sin override, así que la env var exportada gana.
- ⚠️ `/tmp` de WSL se borra si la VM de WSL se reinicia (pasa si matas todos los procesos). Usar `sqlite:///reflex.db` (relativo al proyecto, gitignorado por `*.db`), igual que hace CI.

## Preparar BD y arrancar

```bash
# 1. Migraciones sobre SQLite local (la API de alembic es fiable;
#    `reflex db migrate` a veces termina en silencio sin crear tablas):
.venv/bin/python -c "
from alembic.config import Config
from alembic import command
cfg = Config('alembic.ini')
cfg.set_main_option('sqlalchemy.url', 'sqlite:///reflex.db')
command.upgrade(cfg, 'head')"

# 2. Arrancar (setsid + redirección; sin setsid muere al salir el shell de wsl.exe):
DATABASE_URL='sqlite:///reflex.db' ADMIN_KEY='clave-test' \
  setsid nohup .venv/bin/reflex run --env dev > reflex_verify.log 2>&1 < /dev/null &

# 3. Esperar readiness (~30-60s: compila frontend con bun):
for i in $(seq 1 30); do curl -sf -o /dev/null http://localhost:3000/ && break; sleep 5; done
```

Parar y limpiar: `pkill -f '[r]eflex run'; pkill -f '[g]ranian'; pkill -f '[b]un run dev'; rm -f reflex.db reflex_verify.log`
(⚠️ usar el truco `'[r]eflex'` — un patrón literal se auto-matchea con el propio bash -c y mata tu shell con exit 15).

## Flujos que merece la pena conducir
- Crear liga: `/tournament-config?type=league` → nombre + jugadores → "Guardar Configuración" → dashboard. Duplicados ("Ana"/"ana") deben dar toast de error.
- Marcador: desde el dashboard, "Jugar partido" → `/scoreboard?match_id=N`. Modal "¿Quién comienza sacando?" antes del primer punto; la elección se persiste en `league_matches.initial_server` (verificable con sqlite3).
- Editar participantes: botón lápiz junto a "Standings" (liga) o junto al título (torneo).
- e2e reales: `.venv/bin/python -m pytest tests/e2e -v` con la app corriendo (Chromium de Playwright ya instalado en WSL en ~/.cache/ms-playwright).

## Gotchas del Browser pane embebido
- Las animaciones CSS están congeladas en el pane → los diálogos Radix se quedan con `data-state="closed"` PERO visibles en el DOM (Presence espera animationend que nunca llega). **No es un bug de la app** — verificar el atributo `data-state`, no la presencia en DOM. En Chromium real (e2e) cierran bien.
- `computer{action:"screenshot"}` puede dar timeout con este pane; conducir con `javascript_tool` + `get_page_text` funciona.
- Los toasts (sonner) viven fuera de `<main>`: leerlos con `document.querySelectorAll('[data-sonner-toast]')`.
- Inputs controlados de React: usar el setter nativo + `dispatchEvent(new Event('input', {bubbles:true}))` (form_input del pane también funciona).
