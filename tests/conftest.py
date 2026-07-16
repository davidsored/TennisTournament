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


# ---------------------------------------------------------------------------
# Fixtures de integración — BD SQLite en memoria + mock de rx.session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_db_engine():
    """Engine SQLite en memoria con esquema completo.

    Scope=function: cada test arranca con BD limpia (independencia total).
    """
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    # Importar TODOS los modelos para registrarlos en SQLModel.metadata
    # antes de create_all (orden importante para FKs).
    from TennisTournament.models.league import League  # noqa: F401
    from TennisTournament.models.tournament import Tournament  # noqa: F401
    from TennisTournament.models.league_match import LeagueMatch  # noqa: F401
    from TennisTournament.models.match import Match  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup explícito: drop_all + dispose
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Sesión SQLModel enlazada al engine de test.

    `sqlmodel.Session` extiende la de SQLAlchemy con `.exec()`, que es lo
    que usa el código de producción (states). Cada test recibe una sesión
    nueva sobre una BD vacía.
    """
    from sqlmodel import Session

    session = Session(test_db_engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_rx_session(test_db_session, monkeypatch):
    """Mock de `rx.session()` que redirige a la sesión SQLite de test.

    Reemplaza el context manager de Reflex con uno que devuelve la sesión
    de test, garantizando que NINGÚN test toca Supabase. Si un test
    accidentalmente intentara conectar a producción, este fixture lo
    intercepta.
    """
    from contextlib import contextmanager
    import reflex as rx

    @contextmanager
    def fake_session():
        # Yield la misma sesión de test; los commits del código bajo test
        # quedan en SQLite in-memory y son visibles inmediatamente.
        yield test_db_session

    monkeypatch.setattr(rx, "session", fake_session)
    return test_db_session
