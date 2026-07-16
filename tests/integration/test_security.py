"""Tests de integración de autorización y validación server-side.

Verifican que los mutadores de `LeagueState` están blindados aunque se
invoquen directamente (en Reflex cualquier handler público es invocable
desde el cliente vía WebSocket, saltándose la UI):

- `delete_competition` exige modo admin (check en el mutador, no en la UI).
- `setup_league` / `setup_tournament` rechazan configuraciones inválidas
  (rangos absurdos, nombres duplicados) sin tocar la BD.

No toca Supabase. Usa SQLite en memoria + mock de rx.session().
"""

from __future__ import annotations

import asyncio
import json

import pytest
from sqlmodel import select

from TennisTournament.models.league import League
from TennisTournament.models.league_match import LeagueMatch
from TennisTournament.models.tournament import Tournament
from TennisTournament.states.admin_state import AdminState
from TennisTournament.states.league_state import LeagueState

pytestmark = pytest.mark.integration


ADMIN_KEY = "clave-test-segura"


def _make_league_state() -> LeagueState:
    """Instancia interna del state (patrón de test_casual_integration)."""
    return LeagueState(_reflex_internal_init=True)


def _make_admin_state(token: str) -> AdminState:
    admin = AdminState(_reflex_internal_init=True)
    admin.admin_token = token
    return admin


@pytest.fixture
def admin_env(monkeypatch):
    """Configura ADMIN_KEY en el entorno para la duración del test."""
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)


def _patch_get_state(monkeypatch, admin: AdminState) -> None:
    """Hace que `await self.get_state(AdminState)` devuelva nuestro fake.

    Una instancia interna de State no tiene StateManager, así que el
    `get_state` real no funciona fuera del runtime de Reflex.
    """

    async def fake_get_state(self, cls):
        assert cls is AdminState
        return admin

    monkeypatch.setattr(LeagueState, "get_state", fake_get_state)


def _seed_league(session) -> League:
    """Crea una liga mínima con un partido directamente en la BD de test."""
    league = League(
        name="Liga Test",
        sets_per_match=3,
        games_per_set=6,
        players_json=json.dumps(["Alice", "Bob"]),
    )
    session.add(league)
    session.commit()
    session.refresh(league)
    session.add(
        LeagueMatch(
            league_id=league.id,
            round_num=1,
            leg=1,
            home="Alice",
            away="Bob",
            status="Pendiente",
        )
    )
    session.commit()
    return league


# =============================================================================
# 1. delete_competition exige admin en el mutador
# =============================================================================


class TestDeleteCompetitionAuthorization:
    def test_sin_admin_no_borra(self, mock_rx_session, admin_env, monkeypatch):
        # Arrange: liga en BD y cliente SIN token válido.
        session = mock_rx_session
        league = _seed_league(session)
        _patch_get_state(monkeypatch, _make_admin_state(token=""))
        state = _make_league_state()

        # Act: invocación directa del mutador (simula RPC malicioso).
        result = asyncio.run(state.delete_competition(league.id, "league"))

        # Assert: la liga y sus partidos siguen intactos y hay respuesta
        # (toast de error) en lugar de silencio.
        assert session.get(League, league.id) is not None
        assert (
            len(session.exec(select(LeagueMatch)).all()) == 1
        ), "los partidos no deben borrarse sin admin"
        assert result is not None

    def test_con_admin_borra(self, mock_rx_session, admin_env, monkeypatch):
        # Arrange: mismo escenario pero con el token correcto.
        session = mock_rx_session
        league = _seed_league(session)
        _patch_get_state(monkeypatch, _make_admin_state(token=ADMIN_KEY))
        state = _make_league_state()

        # Act
        result = asyncio.run(state.delete_competition(league.id, "league"))

        # Assert: liga y partidos eliminados; sin toast de error (None).
        assert session.get(League, league.id) is None
        assert len(session.exec(select(LeagueMatch)).all()) == 0
        assert result is None

    def test_token_incorrecto_no_borra(
        self, mock_rx_session, admin_env, monkeypatch
    ):
        session = mock_rx_session
        league = _seed_league(session)
        _patch_get_state(monkeypatch, _make_admin_state(token="otra-clave"))
        state = _make_league_state()

        asyncio.run(state.delete_competition(league.id, "league"))

        assert session.get(League, league.id) is not None

    def test_id_invalido_devuelve_error(
        self, mock_rx_session, admin_env, monkeypatch
    ):
        """Un id no positivo o tipo desconocido no debe reportar éxito."""
        _patch_get_state(monkeypatch, _make_admin_state(token=ADMIN_KEY))
        state = _make_league_state()

        assert asyncio.run(state.delete_competition(0, "league")) is not None
        assert asyncio.run(state.delete_competition("x", "league")) is not None
        assert asyncio.run(state.delete_competition(1, "otro")) is not None

    def test_id_compartido_liga_torneo_solo_borra_el_tipo_pedido(
        self, mock_rx_session, admin_env, monkeypatch
    ):
        """`leagues` y `tournaments` tienen secuencias de id independientes:
        borrar el torneo id=1 no debe tocar la liga id=1."""
        session = mock_rx_session
        league = _seed_league(session)  # League id=1
        tournament = Tournament(
            name="Torneo Test",
            sets_per_match=3,
            games_per_set=6,
            players_json=json.dumps(["Xavi", "Zoe"]),
        )
        session.add(tournament)
        session.commit()
        session.refresh(tournament)
        assert tournament.id == league.id  # colisión real de ids

        _patch_get_state(monkeypatch, _make_admin_state(token=ADMIN_KEY))
        state = _make_league_state()

        result = asyncio.run(
            state.delete_competition(tournament.id, "tournament")
        )

        assert result is None
        assert session.get(Tournament, tournament.id) is None
        assert session.get(League, league.id) is not None, (
            "la liga con el mismo id numérico debe sobrevivir"
        )
        # Los partidos de la liga tampoco deben borrarse.
        assert len(session.exec(select(LeagueMatch)).all()) == 1


# =============================================================================
# 2. setup_league / setup_tournament validan server-side
# =============================================================================


class TestSetupValidationServerSide:
    def test_setup_league_sets_pares_no_crea_filas(self, mock_rx_session):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_league("Liga", ["Alice", "Bob"], sets_per_match=2)

        assert len(session.exec(select(League)).all()) == 0
        assert len(session.exec(select(LeagueMatch)).all()) == 0

    def test_setup_league_games_fuera_de_rango_no_crea_filas(
        self, mock_rx_session
    ):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_league("Liga", ["Alice", "Bob"], games_per_set=0)
        state.setup_league("Liga", ["Alice", "Bob"], games_per_set=13)

        assert len(session.exec(select(League)).all()) == 0

    def test_setup_league_duplicados_no_crea_filas(self, mock_rx_session):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_league("Liga", ["Ana", "ana"])

        assert len(session.exec(select(League)).all()) == 0

    def test_setup_league_valida_crea_filas(self, mock_rx_session):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_league("Liga", ["Alice", "Bob"])

        leagues = session.exec(select(League)).all()
        assert len(leagues) == 1
        # Round Robin x2 con 2 jugadores: 1 ronda, ida + vuelta.
        assert len(session.exec(select(LeagueMatch)).all()) == 2

    def test_setup_tournament_duplicados_no_crea_filas(self, mock_rx_session):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_tournament("Torneo", ["Ana", "ANA", "Bea"])

        assert len(session.exec(select(Tournament)).all()) == 0

    def test_setup_tournament_nombre_reservado_no_crea_filas(
        self, mock_rx_session
    ):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_tournament("Torneo", ["Alice", "BYE"])
        state.setup_tournament("Torneo", ["Alice", "Ganador Partido 1"])

        assert len(session.exec(select(Tournament)).all()) == 0

    def test_setup_tournament_valido_crea_filas(self, mock_rx_session):
        session = mock_rx_session
        state = _make_league_state()

        state.setup_tournament("Torneo", ["Alice", "Bob", "Carol", "Dave"])

        assert len(session.exec(select(Tournament)).all()) == 1
        # Cuadro de 4: 2 semifinales + 1 final.
        assert len(session.exec(select(LeagueMatch)).all()) == 3
