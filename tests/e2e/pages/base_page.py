"""BasePage — superclase con utilidades comunes para todos los Page Objects.

Patrón POM: cada página de la app tiene una clase Python que encapsula
sus localizadores y acciones. Los specs sólo llaman a métodos de Page
Object, nunca tocan `page.locator()` directamente.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


class BasePage:
    """Superclase para todos los Page Objects."""

    # Subclase debe definir su ruta relativa (e.g., "/", "/league-dashboard").
    PATH: str = "/"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    # ------------------------ Navegación ------------------------

    def goto(self, query: str = "") -> "BasePage":
        """Navega a `self.PATH` (+ querystring opcional)."""
        url = f"{self.base_url}{self.PATH}{query}"
        self.page.goto(url)
        self.wait_for_hydration()
        return self

    def wait_for_hydration(self) -> None:
        """Reflex usa WS para hidratar el state. Esperamos a que el body
        tenga contenido antes de empezar a interactuar.
        """
        # Pequeña espera por hidratación. Reflex emite "is-hydrated"
        # como atributo en algunas versiones; si no, usamos networkidle.
        try:
            self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            # En entornos lentos, networkidle puede tardar; seguimos.
            pass

    # ------------------------ Selectores user-centric ------------------------

    def click_button_by_name(self, name: str) -> None:
        """`page.get_by_role('button', name=...)` con espera implícita."""
        self.page.get_by_role("button", name=name).click()

    def click_link_by_name(self, name: str) -> None:
        self.page.get_by_role("link", name=name).click()

    def fill_by_placeholder(self, placeholder: str, value: str) -> None:
        self.page.get_by_placeholder(placeholder).fill(value)

    def fill_by_label(self, label: str, value: str) -> None:
        self.page.get_by_label(label).fill(value)

    def expect_text_visible(self, text: str) -> None:
        expect(self.page.get_by_text(text, exact=False).first).to_be_visible()

    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(
            self.page.url  # noop; se reemplaza con regex abajo
        )
        # `to_have_url` puede aceptar regex; usamos contains via assert fallback
        assert fragment in self.page.url, (
            f"URL actual {self.page.url!r} no contiene {fragment!r}"
        )
