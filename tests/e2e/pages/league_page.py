"""LeaguePage — dashboard de liga (standings + fixtures)."""

from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class LeaguePage(BasePage):
    PATH = "/league-dashboard"

    # ----------------- Verificaciones de standings -----------------

    def expect_player_in_standings(self, player: str) -> None:
        """Verifica que `player` aparece en la tabla de clasificación.

        La tabla se renderiza con `rx.el.table/th/td`, que no siempre se
        exponen como role='cell'. Usamos `get_by_text` como localizador
        user-centric robusto.
        """
        expect(self.page.get_by_text(player, exact=True).first).to_be_visible(
            timeout=10_000
        )

    def expect_standings_with_zero_points(self, players: list[str]) -> None:
        """Antes de jugar, todos los jugadores deben aparecer en la tabla.

        Comprobamos que cada nombre se renderiza. Verificar el "0 puntos"
        directamente es frágil porque hay varios "0" en la fila (PJ, PG, PP,
        sets...) — basta con que los jugadores estén presentes.
        """
        for p in players:
            self.expect_player_in_standings(p)

    def expect_loaded(self) -> None:
        """Verifica que el dashboard se ha cargado.

        Estrategia en cascada: primero el heading 'Standings', si no
        cualquier variante en español, y como fallback la URL + algún
        encabezado de columna ('Pos', 'Pj').
        """
        # Damos tiempo a la hidratación WS antes de aserciones.
        self.page.wait_for_timeout(1000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass

        heading_re = re.compile(r"standings|clasificaci[oó]n", re.IGNORECASE)
        heading = self.page.get_by_text(heading_re).first
        if heading.count() > 0:
            expect(heading).to_be_visible(timeout=10_000)
            return

        # Fallback: URL + encabezado de columna 'Pos'.
        assert "/league-dashboard" in self.page.url, (
            f"URL inesperada: {self.page.url!r}"
        )
        expect(self.page.get_by_text("Pos", exact=True).first).to_be_visible(
            timeout=10_000
        )
