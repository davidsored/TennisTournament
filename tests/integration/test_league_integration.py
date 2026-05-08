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
from typing import TYPE_CHECKING

import pytest

from TennisTournament.logic.fixtures import group_fixtures, FixtureMatch
from TennisTournament.models.league import League, round_robin
from TennisTournament.models.league_match import LeagueMatch

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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
        # Round Robin de 3 jugadores: añade BYE → 4 → 3 rondas (n-1).
        # En cada ronda hay 1 enfrentamiento real (el otro lleva BYE y se descarta).
        # Ida + vuelta = 3 partidos × 2 = 6 matches totales.
        assert len(matches) == 6
        # Verificar que todos están en DB
        db_count = session.query(LeagueMatch).filter_by(league_id=league.id).count()
        assert db_count == 6

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

    def test_3_jugadores_3_rondas_con_bye(self, mock_rx_session):
        # Arrange / Act
        session = mock_rx_session
        league, matches = create_league_with_matches(
            session, name="Test", players=["Alice", "Bob", "Carol"]
        )
        # Assert: con jugadores impares se añade BYE → 4 elementos → n-1 = 3 rondas.
        rondas = set(m.round_num for m in matches)
        assert len(rondas) == 3

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


# =============================================================================
# 5. Standings: lectura desde DB → MatchView → compute_standings
# =============================================================================


class TestStandingsFromDB:
    """Replica el flujo `LeagueState.standings`:
    DB (LeagueMatch) → MatchView → MatchResult → compute_standings.
    """

    def _hydrate_to_match_results(self, session, league_id: int):
        """Simula `_hydrate`: lee LeagueMatch desde DB, los convierte en
        MatchView y luego en MatchResult (lo que recibe `compute_standings`)."""
        from TennisTournament.states.league_state import (
            MatchView,
            _league_match_to_view,
        )
        from TennisTournament.logic.standings import MatchResult

        db_matches = (
            session.query(LeagueMatch).filter_by(league_id=league_id).all()
        )
        # Pasamos por MatchView para asegurar que el flujo real funciona
        views: list[MatchView] = [_league_match_to_view(m) for m in db_matches]
        return [
            MatchResult(
                home=v.home,
                away=v.away,
                sets_home=v.sets_home,
                sets_away=v.sets_away,
                status=v.status,
            )
            for v in views
        ]

    def test_standings_lee_partidos_finalizados_de_db(self, mock_rx_session):
        # Arrange: liga con 3 jugadores y resultados conocidos.
        from TennisTournament.logic.standings import compute_standings

        session = mock_rx_session
        players = ["Alice", "Bob", "Carol"]
        league, matches = create_league_with_matches(
            session, name="LigaTest", players=players
        )

        # Marcamos resultados directamente en DB:
        # Alice 2-0 Bob | Carol 2-1 Alice | Bob 2-1 Carol
        # Resultado: Alice 1V/1D, Bob 1V/1D, Carol 1V/1D — todos a 3 pts.
        # Diferencia de sets:
        #   Alice: ganó 2, perdió (0+1)=1 → diff +1
        #   Bob:   ganó (0+2)=2, perdió (2+1)=3 → diff -1
        #   Carol: ganó (1+2)=3, perdió (1+2)=3 → diff 0
        # Wait, recalculemos: Alice ganó 2 sets vs Bob, perdió 1 set vs Carol → 2-1 → diff +1
        #   Bob: perdió 0 vs Alice, ganó 2 vs Carol, perdió 1 vs Carol → 0+2 / 2+1 → 2-3 → diff -1
        #   Carol: ganó 2 vs Alice, perdió 1 vs Alice, ganó 1 vs Bob → wait this gets confusing.
        # Simplifiquemos: vamos a forzar resultados diferenciados por puntos.
        ida_alice_bob = next(
            m for m in matches if m.leg == 1 and m.home == "Alice" and m.away == "Bob"
        )
        ida_alice_bob.sets_home = 2
        ida_alice_bob.sets_away = 0
        ida_alice_bob.status = "Finalizado"
        session.add(ida_alice_bob)

        # Alice también gana a Carol → Alice tendrá 2 victorias, todos los demás 0
        ida_alice_carol = next(
            m
            for m in matches
            if m.leg == 1
            and ((m.home == "Alice" and m.away == "Carol")
                 or (m.home == "Carol" and m.away == "Alice"))
        )
        if ida_alice_carol.home == "Alice":
            ida_alice_carol.sets_home = 2
            ida_alice_carol.sets_away = 0
        else:
            ida_alice_carol.sets_home = 0
            ida_alice_carol.sets_away = 2
        ida_alice_carol.status = "Finalizado"
        session.add(ida_alice_carol)
        session.commit()

        # Act: replicar el flujo de la propiedad `standings`.
        results = self._hydrate_to_match_results(session, league.id)
        rows = compute_standings(players, results)

        # Assert: Alice debe estar 1ª con 6 pts (2 victorias).
        assert rows[0].player == "Alice"
        assert rows[0].pts == 6
        assert rows[0].pg == 2
        # Bob y Carol con 0 pts (1 derrota cada uno).
        for r in rows[1:]:
            assert r.pts == 0
            assert r.pp == 1

    def test_standings_ignora_partidos_pendientes(self, mock_rx_session):
        # Arrange: ningún partido finalizado.
        from TennisTournament.logic.standings import compute_standings

        session = mock_rx_session
        players = ["Alice", "Bob"]
        league, _ = create_league_with_matches(
            session, name="Sin resultados", players=players
        )

        # Act
        results = self._hydrate_to_match_results(session, league.id)
        rows = compute_standings(players, results)

        # Assert: todos a 0 pts; orden alfabético.
        assert all(r.pts == 0 for r in rows)
        assert [r.player for r in rows] == sorted(players)
        assert all(r.pj == 0 for r in rows)  # ningún PJ contabilizado

    def test_standings_se_actualiza_al_modificar_db(self, mock_rx_session):
        # Arrange: liga vacía, standings inicial todo a 0.
        from TennisTournament.logic.standings import compute_standings

        session = mock_rx_session
        players = ["Alice", "Bob"]
        league, matches = create_league_with_matches(
            session, name="Test", players=players
        )

        # Act 1: leer standings con todo pendiente
        results_1 = self._hydrate_to_match_results(session, league.id)
        rows_1 = compute_standings(players, results_1)
        # Assert 1: 0 pts para todos
        assert all(r.pts == 0 for r in rows_1)

        # Act 2: cerrar un partido en DB (Alice gana ida 2-1)
        ida = next(m for m in matches if m.leg == 1)
        ida.sets_home = 2
        ida.sets_away = 1
        ida.status = "Finalizado"
        session.add(ida)
        session.commit()

        # Act 3: re-leer standings
        results_2 = self._hydrate_to_match_results(session, league.id)
        rows_2 = compute_standings(players, results_2)

        # Assert 2: el ganador (home) tiene 3 pts; el perdedor 0.
        winner = next(r for r in rows_2 if r.player == ida.home)
        loser = next(r for r in rows_2 if r.player == ida.away)
        assert winner.pts == 3
        assert winner.pg == 1
        assert loser.pts == 0
        assert loser.pp == 1

    def test_matchview_propaga_config_games_desde_db(self, mock_rx_session):
        # Arrange: liga con games_per_set=4 (set corto).
        from TennisTournament.states.league_state import _league_match_to_view

        session = mock_rx_session
        league, matches = create_league_with_matches(
            session,
            name="Sets cortos",
            players=["A", "B"],
            sets_per_match=3,
            games_per_set=4,
        )

        # Act: convertir a MatchView (lo que el scoreboard recibirá).
        view = _league_match_to_view(matches[0])

        # Assert: la configuración llega al view sin perderse en el camino.
        assert view.config_games == 4
        assert view.config_sets == 3
