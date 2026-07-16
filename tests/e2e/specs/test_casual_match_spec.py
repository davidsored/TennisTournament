"""E2E Flow D — Partido Amistoso (sin liga ni torneo).

Pasos:
  1. Abrir la app en /.
  2. Pinchar el bento card "Partido Amistoso".
  3. Rellenar nombres de los dos jugadores y ajustar el formato (5 sets / 4 juegos).
  4. Pulsar "Comenzar Partido".
  5. Verificar que la URL es `/scoreboard?casual=1&...` con los params correctos
     y que el marcador en vivo muestra los nombres de los jugadores.
"""

from __future__ import annotations

import pytest

from tests.e2e.pages import CasualPage, HomePage, ScoreboardPage


pytestmark = pytest.mark.e2e


PLAYER_J1 = "Rafa Nadal"
PLAYER_J2 = "Roger Federer"


def test_casual_match_starts_with_correct_players_and_format(page, base_url):
    # Arrange: home cargado y bento de Partido Amistoso visible.
    home = HomePage(page, base_url).goto()
    home.expect_loaded()

    # Act 1: entrar al formulario casual desde el bento card.
    home.click_casual_match()
    casual = CasualPage(page, base_url)
    casual.expect_loaded()

    # Act 2: rellenar nombres y formato no-default para detectar drift de config.
    casual.set_player_j1(PLAYER_J1)
    casual.set_player_j2(PLAYER_J2)
    casual.set_sets_per_match(5)
    casual.set_games_per_set(4)

    # Act 3: comenzar partido → redirect a /scoreboard?casual=1&...
    casual.submit()

    # Assert 1: URL contiene todos los params esperados.
    assert "/scoreboard" in page.url
    assert "casual=1" in page.url
    assert "sets=5" in page.url
    assert "games=4" in page.url
    # Nombres URL-encoded (los espacios pasan como %20).
    assert "Rafa%20Nadal" in page.url
    assert "Roger%20Federer" in page.url

    # Assert 2: el marcador renderiza ambos nombres y el título "Partido Amistoso".
    scoreboard = ScoreboardPage(page, base_url)
    scoreboard.expect_match_title("Partido Amistoso")
    scoreboard.expect_player_names(PLAYER_J1, PLAYER_J2)


def test_casual_match_supports_scoring_after_start(page, base_url):
    """Una vez iniciado el partido casual, los botones de + Punto funcionan."""
    # Arrange + Act: crear partido casual rápido (valores por defecto).
    home = HomePage(page, base_url).goto()
    home.click_casual_match()
    casual = CasualPage(page, base_url)
    casual.expect_loaded()
    casual.set_player_j1("Alice")
    casual.set_player_j2("Bob")
    casual.submit()

    # Act: el modal "¿Quién comienza sacando?" debe aparecer antes del
    # primer punto; elegimos a Bob (J2) como primer sacador.
    scoreboard = ScoreboardPage(page, base_url)
    scoreboard.expect_player_names("Alice", "Bob")
    scoreboard.choose_server(player_num=2)

    # Act: sumar un punto a cada jugador; el state debe aceptarlos sin error.
    scoreboard.add_point_to_j1()
    page.wait_for_timeout(200)
    scoreboard.add_point_to_j2()
    page.wait_for_timeout(200)

    # Assert: seguimos en el marcador casual (no hubo redirect inesperado).
    assert "casual=1" in page.url
    # El banner "¡Partido Finalizado!" NO debe aparecer todavía.
    assert (
        page.get_by_text("¡Partido Finalizado!", exact=False).count() == 0
    )

    # Assert: al refrescar un partido con progreso, el modal de saque NO
    # vuelve a aparecer (la elección vive en el estado de sesión).
    page.reload()
    page.wait_for_timeout(1500)
    scoreboard.expect_player_names("Alice", "Bob")
    scoreboard.expect_no_server_modal()
