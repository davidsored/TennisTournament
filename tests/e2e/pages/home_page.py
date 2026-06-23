"""HomePage — pantalla de inicio con bento grid (Liga / Torneo)."""

from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class HomePage(BasePage):
    PATH = "/"

    # ------------------------ Acciones ------------------------

    def click_create_league(self) -> None:
        """Pincha el bento card 'Crear Liga' (NO el botón 'Crear competición'
        del estado vacío de Recientes).

        Usamos `get_by_text(..., exact=True)` para fijar el match al título
        del bento card y subimos al ancestro `<a>` para hacer click.
        """
        title = self.page.get_by_text("Crear Liga", exact=True).first
        # Sube al primer ancestro <a> (el bento card es un link).
        link = title.locator("xpath=ancestor::a[1]")
        link.click()
        self.page.wait_for_timeout(1000)  # hidratación tras navegar
        self.wait_for_hydration()

    def click_create_tournament(self) -> None:
        """Pincha el bento card 'Crear Torneo' (NO 'Crear competición')."""
        title = self.page.get_by_text("Crear Torneo", exact=True).first
        link = title.locator("xpath=ancestor::a[1]")
        link.click()
        self.page.wait_for_timeout(1000)  # hidratación tras navegar
        self.wait_for_hydration()

    def click_casual_match(self) -> None:
        """Pincha el bento card 'Partido Amistoso' (acceso directo sin liga)."""
        title = self.page.get_by_text("Partido Amistoso", exact=True).first
        link = title.locator("xpath=ancestor::a[1]")
        link.click()
        self.page.wait_for_timeout(1000)
        self.wait_for_hydration()

    # ------------------------ Verificaciones ------------------------

    def expect_loaded(self) -> None:
        # Buscamos el heading de bento — debe ser visible al cargar.
        expect(self.page.get_by_text("Crear Liga", exact=True).first).to_be_visible()
        expect(
            self.page.get_by_text("Crear Torneo", exact=True).first
        ).to_be_visible()

    def expect_recent_competition(self, name: str) -> None:
        """Verifica que una competición aparece en el listado 'Recientes'."""
        expect(self.page.get_by_text(name, exact=False).first).to_be_visible()
