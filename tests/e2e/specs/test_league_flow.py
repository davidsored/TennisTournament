"""E2E Flow A — Ciclo de vida de Liga.

Pasos:
  1. Abrir la app en /.
  2. Crear una liga "E2E Liga 4 juegos" con 3 jugadores y 4 juegos por set.
  3. Verificar que el dashboard de liga muestra los 3 nombres en la
     tabla de clasificación, todos con 0 puntos (sin partidos jugados).
"""

from __future__ import annotations

import pytest

from tests.e2e.pages import ConfigPage, HomePage, LeaguePage


pytestmark = pytest.mark.e2e

LEAGUE_NAME = "E2E Liga 4 juegos"
PLAYERS = ["Alice", "Bob", "Carol"]


def test_league_lifecycle_create_and_view_standings(page, base_url):
    # Arrange: home cargado
    home = HomePage(page, base_url).goto()
    home.expect_loaded()

    # Act 1: ir a config con type=league
    home.click_create_league()
    config = ConfigPage(page, base_url)
    config.expect_loaded()

    # Act 2: rellenar formulario (nombre, juegos por set=4, jugadores)
    config.set_name(LEAGUE_NAME)
    config.set_games_per_set(4)
    config.add_players(PLAYERS)
    config.submit()

    # Act 3: tras submit, debería redirigir al dashboard de liga.
    league = LeaguePage(page, base_url)
    league.expect_loaded()

    # Assert: los 3 jugadores aparecen y standings está a 0.
    league.expect_standings_with_zero_points(PLAYERS)


def test_league_appears_in_recent_competitions(page, base_url):
    # Arrange + Act: crear liga (mismo flujo)
    home = HomePage(page, base_url).goto()
    home.click_create_league()
    config = ConfigPage(page, base_url)
    config.set_name("E2E Recent Test")
    config.add_players(["P1", "P2"])
    config.submit()

    # Act: volver al home
    HomePage(page, base_url).goto()

    # Assert: la liga aparece en "Competiciones Recientes"
    HomePage(page, base_url).expect_recent_competition("E2E Recent Test")
