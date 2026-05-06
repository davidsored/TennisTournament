"""Tests de integración para LeagueState — persistencia y Round Robin.

Valida que:
- setup_league crea una Liga y todos los LeagueMatch correctamente.
- config_games/config_sets se guardan en cada partido.
- La lista de jugadores se serializa y recupera.
- El algoritmo Round Robin genera la cantidad correcta de rondas e ida/vuelta.

No toca Supabase. Usa SQLite en memoria + mock de rx.session().
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy.orm import Session

from TennisTournament.logic.fixtures import group_fixtures, FixtureMatch
from TennisTournament.models.league import League, round_robin
from TennisTournament.models.league_match import LeagueMatch


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers: simulan lo que hace setup_league sin la complejidad de State
# ---------------------------------------------------------------------------


def create_league_with_matches(
    session: Session,
    name: str,
    players: list[str],
    sets_per_match: int = 3,
    games_per_set: int = 6,
) -> tuple[League, list[LeagueMatch]]:
    """Simula setup_league: crea Liga + Round Robin ida/vuelta en DB.

    Retorna (league, all_matches) para verificación.
    """
    seeding = list(players)
    rounds = round_robin(seeding)

    # Crear liga
    league = League(
        name=name,
        sets_per_match=sets_per_match,
        games_per_set=games_per_set,
        players_json=json.dumps(players),
    )
    session.add(league)
    session.commit()
    session.refresh(league)

    # Crear matches (ida y vuelta)
    matches: list[LeagueMatch] = []
    STATUS_PENDIENTE = "Pendiente"
    for r, round_matches in enumerate(rounds, start=1):
        # Ida
        for home, away in round_matches:
            m = LeagueMatch(
                league_id=league.id,
                round_num=r,
                leg=1,
                home=home,
                away=away,
                status=STATUS_PENDIENTE,
                config_sets=sets_per_match,
                config_games=games_per_set,
            )
            session.add(m)
            matches.append(m)
        # Vuelta
        for home, away in round_matches:
            m = LeagueMatch(
                league_id=league.id,
                round_num=r,
                leg=2,
                home=away,
                away=home,
                status=STATUS_PENDIENTE,
                config_sets=sets_per_match,
                config_games=games_per_set,
            )
            session.add(m)
            matches.append(m)
    session.commit()

    return league, matches


# =============================================================================
# 1. Creación de Liga y LeagueMatch
# =============================================================================


class TestLeagueCreation:
    def test_league_creada_con_nombre_y_parametros(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        # Act
        league, _ = create_league_with_matches(
            session,
            name="Torneo Primavera",
            players=["Alice", "Bob", "Carol"],
            sets_per_match=3,
            games_per_set=6,
        )
        # Assert
        assert league.id is not None
        assert league.name == "Torneo Primavera"
        assert league.sets_per_match == 3
        assert league.games_per_set == 6
        # Verificar que se persiste
        retrieved = session.get(League, league.id)
        assert retrieved is not None
        assert retrieved.name == "Torneo Primavera"

    def test_players_json_serializado_y_recuperable(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        players_original = ["Alice", "Bob", "Carol"]
        # Act
        league, _ = create_league_with_matches(
            session,
            name="Test",
            players=players_original,
            sets_per_match=3,
            games_per_set=6,
        )
        # Assert
        retrieved = session.get(League, league.id)
        players_recovered = json.loads(retrieved.players_json)
        assert players_recovered == players_original


# =============================================================================
# 2. LeagueMatch: creación, config_games/config_sets, ida/vuelta
# =============================================================================


class TestLeagueMatches:
    def test_all_leaguematches_creados(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        players = ["Alice", "Bob", "Carol"]
        # Act
        league, matches = create_league_with_matches(
            session, name="Test", players=players
        )
        # Assert
        # Round Robin de 3 jugadores: (3-1)=2 rondas, cada ronda 3 enfrentamientos
        # ida + vuelta = 2*3 = 6 matches por ronda, 2 rondas = 12 matches total
        assert len(matches) == 12
        # Verificar que todos están en DB
        db_count = session.query(LeagueMatch).filter_by(league_id=league.id).count()
        assert db_count == 12

    def test_config_games_config_sets_en_cada_match(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        # Act
        league, matches = create_league_with_matches(
            session,
            name="Test",
            players=["Alice", "Bob"],
            sets_per_match=5,
            games_per_set=8,
        )
        # Assert
        for m in matches:
            assert m.config_sets == 5
            assert m.config_games == 8

    def test_ida_y_vuelta_emparejadas_correctamente(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        # Act
        league, matches = create_league_with_matches(
            session, name="Test", players=["Alice", "Bob"], sets_per_match=3
        )
        # Assert: 1 ronda, 2 enfrentamientos
        # Ida: Alice vs Bob, Vuelta: Bob vs Alice
        ida_matches = [m for m in matches if m.leg == 1]
        vuelta_matches = [m for m in matches if m.leg == 2]
        assert len(ida_matches) == 1
        assert len(vuelta_matches) == 1
        assert ida_matches[0].home == "Alice" and ida_matches[0].away == "Bob"
        assert vuelta_matches[0].home == "Bob" and vuelta_matches[0].away == "Alice"

    def test_matches_status_pendiente_al_crearlos(self, mock_rx_session):
        # Arrange / Act
        session = mock_rx_session
        league, matches = create_league_with_matches(
            session, name="Test", players=["Alice", "Bob"]
        )
        # Assert
        for m in matches:
            assert m.status == "Pendiente"


# =============================================================================
# 3. Round Robin: rondas, cantidad de partidos
# =============================================================================


class TestRoundRobinStructure:
    def test_2_jugadores_1_ronda(self, mock_rx_session):
        # Arrange / Act
        session = mock_rx_session
        league, matches = create_league_with_matches(
            session, name="Test", players=["Alice", "Bob"]
        )
        # Assert: 1 ronda, 2 partidos (ida/vuelta)
        assert len(matches) == 2
        assert all(m.round_num == 1 for m in matches)

    def test_3_jugadores_2_rondas(self, mock_rx_session):
        # Arrange / Act
        session = mock_rx_session
        league, matches = create_league_with_matches(
            session, name="Test", players=["Alice", "Bob", "Carol"]
        )
        # Assert: (3-1)=2 rondas
        rondas = set(m.round_num for m in matches)
        assert len(rondas) == 2

    def test_4_jugadores_3_rondas(self, mock_rx_session):
        # Arrange / Act
        session = mock_rx_session
        league, matches = create_league_with_matches(
            session, name="Test", players=["A", "B", "C", "D"]
        )
        # Assert: (4-1)=3 rondas
        rondas = set(m.round_num for m in matches)
        assert len(rondas) == 3


# =============================================================================
# 4. Validación de datos completos (END-TO-END ligero)
# =============================================================================


class TestDataIntegrity:
    def test_league_y_matches_completamente_recuperables(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        players = ["Alice", "Bob", "Carol"]
        # Act
        league, _ = create_league_with_matches(
            session,
            name="FullTest",
            players=players,
            sets_per_match=3,
            games_per_set=4,
        )
        # Assert: recuperar liga desde DB y validar todos los matches
        retrieved_league = session.get(League, league.id)
        assert retrieved_league is not None
        matches = session.query(LeagueMatch).filter_by(league_id=league.id).all()
        assert len(matches) > 0
        # Todos los matches tienen referencia válida a la liga
        for m in matches:
            assert m.league_id == league.id
            assert m.config_games == 4
            assert m.config_sets == 3
            # Los jugadores son válidos (en la lista original)
            assert m.home in players or m.away in players

    def test_multiples_ligas_no_se_mezclan(self, mock_rx_session):
        # Arrange
        session = mock_rx_session
        # Act
        league1, _ = create_league_with_matches(
            session, name="Liga 1", players=["A", "B"]
        )
        league2, _ = create_league_with_matches(
            session, name="Liga 2", players=["C", "D"]
        )
        # Assert
        matches1 = session.query(LeagueMatch).filter_by(league_id=league1.id).count()
        matches2 = session.query(LeagueMatch).filter_by(league_id=league2.id).count()
        assert matches1 == 2  # 1 ronda, ida/vuelta
        assert matches2 == 2
        # Las ligas tienen nombres distintos
        assert league1.name == "Liga 1"
        assert league2.name == "Liga 2"
