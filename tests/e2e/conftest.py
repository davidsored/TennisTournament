"""Configuración Playwright para tests E2E.

- `BASE_URL`: Reflex se expone en http://localhost:3000 (frontend) por defecto.
  Puede sobreescribirse con la env var `E2E_BASE_URL`.
- `browser_context_args`: tamaño de viewport y locale.
- `playwright_config`: timeouts generosos porque Reflex hidrata el state vía WS.

Aislamiento de DB: estos tests asumen que el backend apunta a una BD efímera
(SQLite local o Supabase de staging). NUNCA ejecutar contra producción.
"""

from __future__ import annotations

import os

import pytest


# Permite cambiar el target con env var; útil para CI o testing remoto.
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override por defecto de pytest-playwright."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "locale": "es-ES",
        # Reduce ruido de animaciones en CI.
        "reduced_motion": "reduce",
    }


@pytest.fixture
def page(page, base_url, request):
    """Page con timeout elevado para Reflex (hidratación WS) y screenshot
    automático en caso de fallo del test.
    """
    page.set_default_timeout(15_000)         # 15 s por acción
    page.set_default_navigation_timeout(30_000)
    yield page

    # Captura post-test si el test ha fallado (rep_call lo setea el hook).
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        try:
            test_id = request.node.name.replace("/", "_").replace("::", "_")
            path = f"debug_fail_{test_id}.png"
            page.screenshot(path=path, full_page=True)
            print(f"\n[E2E] Screenshot del fallo guardado en: {path}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n[E2E] No se pudo capturar screenshot: {exc}")


# ---------------------------------------------------------------------------
# Hook que expone `request.node.rep_call` con el resultado del test
# ---------------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Adjunta a `item` el reporte de cada fase (setup, call, teardown).

    Patrón estándar (recomendado por la doc de pytest) para que las fixtures
    puedan inspeccionar si el test ha pasado o fallado durante el yield.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
