"""E2E Flow C — Persistencia de configuración global (tema oscuro/claro).

Pasos:
  1. Cargar el home y leer el tema actual (atributo `class` del <html>).
  2. Pulsar el toggle de tema (si existe). Verificar que cambia.
  3. Navegar a /league-dashboard. Verificar que el nuevo tema persiste
     (rx.LocalStorage debería mantenerlo entre páginas).

Si la app no tiene un toggle visible de tema, el test se skipea.
"""

from __future__ import annotations

import pytest

from tests.e2e.pages import HomePage


pytestmark = pytest.mark.e2e


def _read_theme_class(page) -> str:
    """Devuelve el atributo class del <html>, donde Reflex inyecta 'dark'."""
    return page.evaluate("document.documentElement.className") or ""


def test_theme_persists_across_navigation(page, base_url):
    # Arrange
    home = HomePage(page, base_url).goto()
    home.expect_loaded()
    initial_theme = _read_theme_class(page)

    # Act 1: localizar el toggle de tema. Probamos varios candidatos.
    candidates = [
        "Cambiar tema",
        "Modo oscuro",
        "Modo claro",
        "Toggle theme",
    ]
    toggle = None
    for label in candidates:
        loc = page.get_by_role("button", name=label)
        if loc.count() > 0:
            toggle = loc.first
            break
    if toggle is None:
        pytest.skip("La app no expone un toggle de tema accesible.")

    toggle.click()
    page.wait_for_timeout(300)  # animación + state propagation
    new_theme = _read_theme_class(page)
    assert new_theme != initial_theme, (
        f"El toggle no cambió el tema (antes: {initial_theme!r}, "
        f"después: {new_theme!r})"
    )

    # Act 2: navegar a otra página
    page.goto(f"{base_url}/league")
    page.wait_for_load_state("networkidle")

    # Assert: el tema persiste tras la navegación
    persisted_theme = _read_theme_class(page)
    assert persisted_theme == new_theme, (
        f"El tema no persistió tras navegar (esperado {new_theme!r}, "
        f"actual {persisted_theme!r})"
    )
