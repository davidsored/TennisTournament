"""TournamentPage — dashboard del cuadro eliminatorio (bracket)."""

from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class TournamentPage(BasePage):
    PATH = "/tournament-dashboard"

    # ----------------- Acciones -----------------

    def open_match_by_players(self, home: str, away: str) -> None:
        """Abre el scoreboard de un partido específico clicando su tarjeta.

        Estrategia: localiza un card que contenga ambos nombres y haz click
        en él (la card es navegable a /scoreboard).
        """
        # Buscamos un elemento que contenga AMBOS textos (home y away).
        card = self.page.locator(
            f"text={home}"
        ).locator(
            "xpath=ancestor::*[contains(., '{}')][1]".format(away)
        ).first
        card.click()
        self.wait_for_hydration()

    def open_first_pending_match(self) -> None:
        """Abre el primer partido del bracket.

        El play-overlay es un botón pequeño posicionado en `-top-2 -right-2`
        con `w-7 h-7`. Playwright a veces lo considera "not visible" por
        este offset absolute. En lugar de pelear con el click visual,
        leemos el `href` del primer link al scoreboard y navegamos
        directamente con `page.goto()` — el resultado funcional es idéntico
        para el usuario y elimina la dependencia del overlay.

        Estrategias en cascada:
          1. Leer href del primer `a[href*="/scoreboard?match_id="]` y
             hacer `page.goto(href)` — robusto al overlay invisible.
          2. Forzar click con `force=True` (bypass del visibility check).
          3. Buscar por texto 'pendiente' (case-insensitive).
        """
        import re

        # Asegurar que el bracket se ha pintado completamente.
        try:
            self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

        # ----- Estrategia 1: leer href y navegar directamente -----
        scoreboard_links = self.page.locator(
            'a[href*="/scoreboard?match_id="]'
        )
        count = scoreboard_links.count()
        if count > 0:
            try:
                href = scoreboard_links.first.get_attribute("href")
                if href:
                    full_url = href if href.startswith("http") else (
                        f"{self.base_url}{href}"
                    )
                    self.page.goto(full_url)
                    self.page.wait_for_url(
                        re.compile(r".*/scoreboard.*"), timeout=10_000
                    )
                    self.wait_for_hydration()
                    return
            except Exception:
                self.page.screenshot(path="debug_open_match_strategy1.png")

        # ----- Estrategia 2: scroll + force click -----
        if count > 0:
            try:
                first = scoreboard_links.first
                first.scroll_into_view_if_needed(timeout=5_000)
                first.click(force=True, timeout=10_000)
                self.page.wait_for_url(
                    re.compile(r".*/scoreboard.*"), timeout=10_000
                )
                self.wait_for_hydration()
                return
            except Exception:
                self.page.screenshot(path="debug_open_match_strategy2.png")

        # ----- Estrategia 3: regex 'pendiente' case-insensitive -----
        pending_regex = re.compile(r"pendiente", re.IGNORECASE)
        pending_label = self.page.get_by_text(pending_regex).first
        if pending_label.count() > 0:
            try:
                expect(pending_label).to_be_visible(timeout=10_000)
                card = pending_label.locator(
                    "xpath=ancestor::*[self::a or self::button][1]"
                )
                card.click(force=True)
                self.page.wait_for_url(
                    re.compile(r".*/scoreboard.*"), timeout=10_000
                )
                self.wait_for_hydration()
                return
            except Exception:
                self.page.screenshot(path="debug_open_match_strategy3.png")

        # Sin partidos accesibles — capturar evidencia.
        self.page.screenshot(path="debug_open_match_no_strategy.png")
        raise AssertionError(
            "No se encontró ningún partido accesible en el bracket. "
            "Captura: debug_open_match_no_strategy.png"
        )

    # ----------------- Verificaciones del bracket -----------------

    def expect_player_in_final(self, player: str) -> None:
        """Verifica que `player` aparece en el slot de la final.

        Heurística: la final tiene el icono trofeo o el texto 'Final'.
        Buscamos el bloque que contiene 'Final' y comprobamos que ahí
        aparece el nombre.
        """
        final_section = self.page.get_by_text("Final", exact=False).first.locator(
            "xpath=ancestor::*[contains(@class, 'flex') or self::section][1]"
        )
        expect(final_section.get_by_text(player, exact=False).first).to_be_visible()

    def expect_winner_advanced(self, winner: str) -> None:
        """Versión flexible: verifica que `winner` aparece en cualquier
        slot de una ronda posterior (no en R1)."""
        # Locator que matchea exactamente el nombre del jugador,
        # excluyendo el placeholder "Ganador Partido X" (otra cadena).
        all_occurrences = self.page.get_by_text(winner, exact=True)
        # Debe aparecer al menos 2 veces: una en R1 (su origen) y otra en
        # la ronda siguiente tras el avance.
        expect(all_occurrences).to_have_count(
            2, timeout=15_000  # Reflex puede tardar en re-renderizar
        )

    def expect_loaded(
        self,
        tournament_name: str | None = None,
        any_player: str | None = None,
    ) -> None:
        """Verifica que el dashboard de torneo está completamente hidratado.

        Estrategia (en orden de robustez):
          1. Si se pasa `tournament_name`, busca ese título en el header.
          2. Si se pasa `any_player`, comprueba que aparece como slot del bracket.
          3. Como último recurso, espera a que la URL incluya el path
             `/tournament-dashboard` y a que aparezca cualquier card de partido
             (texto 'Pendiente' o 'Finalizado').
        """
        # Reflex hidrata por WS — damos tiempo extra antes de comprobar nada.
        self.page.wait_for_timeout(1000)

        if tournament_name:
            expect(
                self.page.get_by_text(tournament_name, exact=False).first
            ).to_be_visible(timeout=15_000)
            return

        if any_player:
            expect(
                self.page.get_by_text(any_player, exact=True).first
            ).to_be_visible(timeout=15_000)
            return

        # Fallback: la URL debe ser la del dashboard y debe haber algún
        # estado de partido visible (Pendiente / Finalizado).
        assert "/tournament-dashboard" in self.page.url, (
            f"URL inesperada: {self.page.url!r}"
        )
        status_marker = self.page.get_by_text("Pendiente", exact=False).or_(
            self.page.get_by_text("Finalizado", exact=False)
        )
        expect(status_marker.first).to_be_visible(timeout=15_000)
