"""Configuración global de pytest.

- Inserta la raíz del proyecto en `sys.path` para poder importar el paquete
  `TennisTournament` sin instalación editable.
- Define fixtures comunes (jugadores, partidos vacíos, resultados) reutilizables
  por todas las suites unitarias.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Fixtures comunes — sin estado, sin DB, sin Reflex
# ---------------------------------------------------------------------------


@pytest.fixture
def players_4() -> list[str]:
    """4 jugadores reales (potencia exacta de 2)."""
    return ["Alice", "Bob", "Carol", "Dave"]


@pytest.fixture
def players_5() -> list[str]:
    """5 jugadores reales (fuerza un cuadro de 8 con 3 BYEs)."""
    return ["Alice", "Bob", "Carol", "Dave", "Eve"]


@pytest.fixture
def players_8() -> list[str]:
    """8 jugadores reales (potencia exacta de 2)."""
    return ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi"]


@pytest.fixture
def fresh_match():
    """Factoría de partidos limpios al mejor de N sets / M juegos.

    Devuelve una función `make(best_of=3, games=6)` para que cada test ajuste
    la configuración sin contaminar a otros.
    """
    from TennisTournament.models.match import Match

    def make(best_of: int = 3, games: int = 6) -> Match:
        return Match(
            player_j1="Alice",
            player_j2="Bob",
            config_sets=best_of,
            config_games=games,
        )

    return make
