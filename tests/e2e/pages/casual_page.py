"""CasualPage — formulario rápido de "Partido Amistoso".

Encapsula la página `/casual-match`:
- Inputs de nombres de los dos jugadores.
- Steppers de "Sets por partido" y "Juegos por set".
- Botón "Comenzar Partido" que redirige a `/scoreboard?casual=1&...`.

La estrategia de localización es la misma que en `ConfigPage`: selectores
user-centric (placeholders, texto de labels) y subida al ancestro común
para los steppers. Resistente a cambios menores de wrappers/classes.
"""

from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class CasualPage(BasePage):
    PATH = "/casual-match"

    # ----------------- Acciones de formulario -----------------

    def set_player_j1(self, name: str) -> None:
        self.fill_by_placeholder("Nombre del jugador 1", name)

    def set_player_j2(self, name: str) -> None:
        self.fill_by_placeholder("Nombre del jugador 2", name)

    def set_sets_per_match(self, target: int) -> None:
        self._adjust_stepper("Sets por partido", target)

    def set_games_per_set(self, target: int) -> None:
        self._adjust_stepper("Juegos por set", target)

    def submit(self) -> None:
        """Pulsa "Comenzar Partido" y espera el redirect al marcador.

        El handler `start_match` valida y devuelve `rx.redirect(...)`. Esperamos
        explícitamente a que la URL contenga `/scoreboard?casual=1` antes de
        ceder el control — si quedamos en el formulario sería porque la
        validación falló (toast) y queremos detectarlo cuanto antes.
        """
        self.page.get_by_role("button", name="Comenzar Partido").click()
        try:
            self.page.wait_for_url(
                re.compile(r".*/scoreboard\?casual=1.*"),
                timeout=15_000,
            )
        except Exception:
            self.page.screenshot(path="debug_casual_no_redirect.png")
            raise
        # Hidratación del scoreboard tras el redirect.
        self.page.wait_for_timeout(1000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass

    # ----------------- Helpers (idénticos a ConfigPage) -----------------

    def _stepper_section(self, label_text: str):
        """Localiza el contenedor del stepper indicado subiendo al primer
        ancestro `<div>` que contenga al menos 2 botones (− y +).
        """
        label_el = self.page.get_by_text(label_text, exact=False).first
        return label_el.locator(
            "xpath=ancestor::div[count(.//button) >= 2][1]"
        )

    def _adjust_stepper(self, label_text: str, target: int) -> None:
        section = self._stepper_section(label_text)
        section.first.wait_for(state="visible", timeout=10_000)
        buttons = section.locator("button")
        minus_btn = buttons.nth(0)
        plus_btn = buttons.nth(1)
        for _ in range(20):  # safety cap
            current = self._read_stepper_value(section)
            if current == target:
                return
            if current < target:
                plus_btn.click()
            else:
                minus_btn.click()
            self.page.wait_for_timeout(120)

    @staticmethod
    def _read_stepper_value(section_locator) -> int:
        spans = section_locator.locator("span")
        n = spans.count()
        for i in range(n):
            text = spans.nth(i).inner_text().strip()
            if text.isdigit():
                return int(text)
        return 0

    # ----------------- Verificaciones -----------------

    def expect_loaded(self) -> None:
        expect(
            self.page.get_by_text("Jugadores", exact=False).first
        ).to_be_visible(timeout=10_000)
        expect(
            self.page.get_by_text("Formato de Partido", exact=False).first
        ).to_be_visible()
