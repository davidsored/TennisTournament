"""ScoreboardPage — marcador en vivo con botones para sumar puntos."""

from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class ScoreboardPage(BasePage):
    PATH = "/scoreboard"

    # ----------------- Acciones -----------------

    def add_point_to_j1(self) -> None:
        """Suma un punto al jugador 1 (botón izquierdo).

        Los `_point_button` reales no tienen aria-label: son `<button>` con
        dos spans (nombre del jugador + texto "+ Punto"). Hay exactamente
        dos en la pantalla → el primero es J1, el segundo es J2.
        """
        self._point_buttons().nth(0).click()

    def add_point_to_j2(self) -> None:
        """Suma un punto al jugador 2 (botón derecho)."""
        self._point_buttons().nth(1).click()

    def _point_buttons(self):
        """Locator de los dos botones de sumar punto.

        Estrategia: cualquier `<button>` que contenga el texto "Punto".
        Es resistente a mayúsculas/minúsculas y a cambios menores de
        formato porque coincide con el span "+ Punto" de `_point_button`.
        """
        import re

        return self.page.get_by_role(
            "button", name=re.compile(r"punto", re.IGNORECASE)
        )

    def win_match_for_player(self, player_num: int, max_clicks: int = 60) -> None:
        """Sube puntos al jugador `player_num` (1 o 2) hasta que el partido
        termine. Best of 3 / 6 juegos por set ⇒ 24 puntos limpios bastan.

        El loop se detiene cuando aparece el banner "Finalizado" o el
        contador alcanza `max_clicks` (safety net).
        """
        # Espera inicial para que el scoreboard hidrate por completo.
        self.page.wait_for_timeout(1000)
        for _ in range(max_clicks):
            # ¿Ya está finalizado?
            if self._is_finished():
                return
            if player_num == 1:
                self.add_point_to_j1()
            else:
                self.add_point_to_j2()
            # Espera tras cada click — Reflex propaga el state por WS y a
            # veces el siguiente click llega antes de que el botón esté listo.
            self.page.wait_for_timeout(150)

    def back_to_dashboard(self) -> None:
        """Pulsa 'Finalizar partido' (footer) y espera el redirect al bracket.

        El partido sólo se marca como finalizado en BD y se vuelve al bracket
        cuando el usuario pulsa este botón — no es automático tras el último
        punto. Tras el redirect forzamos un `reload()` para que Reflex
        re-hidrate el state desde DB con el ganador propagado al next_match.
        """
        import re

        finalize_btn = self.page.get_by_role(
            "button", name="Finalizar partido"
        )
        if finalize_btn.count() > 0:
            finalize_btn.first.click()
            # Esperar el redirect explícito al dashboard correcto.
            try:
                self.page.wait_for_url(
                    re.compile(r".*/(tournament|league)-dashboard.*"),
                    timeout=15_000,
                )
            except Exception:
                self.page.screenshot(path="debug_finish_no_redirect.png")
                raise
            # Forzar rehidratación del state desde DB para que el bracket
            # refleje el ganador en el siguiente slot.
            self.page.reload()
            self.page.wait_for_timeout(1500)
            try:
                self.page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                pass
            return
        # Fallback robusto: navegación directa al dashboard de torneo.
        self.page.go_back()
        self.page.wait_for_timeout(1500)
        self.wait_for_hydration()

    # ----------------- Verificaciones -----------------

    def expect_finished(self) -> None:
        # Banner "¡Partido Finalizado!" sólo aparece tras cierre real del match.
        expect(
            self.page.get_by_text("¡Partido Finalizado!", exact=False).first
        ).to_be_visible(timeout=15_000)

    # ----------------- Helpers -----------------

    def _is_finished(self) -> bool:
        """True cuando aparece el banner '¡Partido Finalizado!'.

        No usamos 'Finalizado' a secas porque ese texto puede aparecer
        antes (en el label de estado) y daría falsos positivos.
        """
        try:
            loc = self.page.get_by_text("¡Partido Finalizado!", exact=False)
            return loc.count() > 0 and loc.first.is_visible()
        except Exception:
            return False
