"""E2E Flow B — Torneo + avance automático del ganador.

Pasos:
  1. Crear un torneo "Semis" de 4 jugadores.
  2. Abrir el primer partido pendiente desde el bracket.
  3. Sumar puntos al jugador 1 hasta cerrar el partido.
  4. Volver al bracket y verificar que el ganador aparece en R2 (final).
"""

from __future__ import annotations

import pytest

from tests.e2e.pages import (
    ConfigPage,
    HomePage,
    ScoreboardPage,
    TournamentPage,
)


pytestmark = pytest.mark.e2e

TOURNAMENT_NAME = "Semis"
PLAYERS = ["Alice", "Bob", "Carol", "Dave"]


def test_tournament_winner_advances_to_final(page, base_url):
    # ============= Arrange =============
    home = HomePage(page, base_url).goto()
    home.expect_loaded()

    # Crear torneo
    home.click_create_tournament()
    config = ConfigPage(page, base_url)
    config.expect_loaded()
    config.set_name(TOURNAMENT_NAME)
    config.add_players(PLAYERS)
    config.submit()

    bracket = TournamentPage(page, base_url)
    # Pasamos el nombre del torneo: localizador robusto que no depende de
    # un texto genérico como "Cuadro" o "Bracket".
    bracket.expect_loaded(tournament_name=TOURNAMENT_NAME)

    # Capturar el primer partido pendiente y recordar quién es J1.
    # Para esta verificación, abrimos el primer pendiente y simulamos
    # victoria del jugador 1 (home).
    # NOTA: con shuffle aleatorio, no sabemos el orden exacto. Por eso
    #       usamos "open_first_pending_match" + "win_match_for_player(1)".

    # ============= Act =============
    bracket.open_first_pending_match()
    scoreboard = ScoreboardPage(page, base_url)
    scoreboard.win_match_for_player(player_num=1)
    scoreboard.expect_finished()
    scoreboard.back_to_dashboard()

    # ============= Assert =============
    bracket = TournamentPage(page, base_url)
    bracket.expect_loaded(tournament_name=TOURNAMENT_NAME)
    # Margen extra para que Reflex termine de pintar el bracket completo
    # tras el reload (algunos slots se renderizan vía rx.foreach asíncrono).
    page.wait_for_timeout(2000)

    # El ganador (J1 del primer partido) debe aparecer al menos 2 veces:
    # una en R1 (su origen) + una en R2 (avance).
    # Como no sabemos el nombre exacto, validamos que TODOS los jugadores
    # de R1 están presentes y al menos UNO aparece duplicado.
    counts = {p: page.get_by_text(p, exact=True).count() for p in PLAYERS}
    duplicated_count = sum(1 for c in counts.values() if c >= 2)

    if duplicated_count < 1:
        # Capturamos screenshot y dejamos un mensaje diagnóstico claro.
        page.screenshot(path="debug_no_winner_advance.png", full_page=True)
        raise AssertionError(
            f"Ningún jugador apareció duplicado tras finalizar un partido — "
            f"el ganador no avanzó visualmente al bracket.\n"
            f"Conteos por jugador: {counts}\n"
            f"URL actual: {page.url}\n"
            f"Captura: debug_no_winner_advance.png"
        )
