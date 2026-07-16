"""Tests de integración de `LeagueState.rename_player` (renombrado transaccional).

El nombre de un participante vive desnormalizado en `players_json` de la
competición y en `home`/`away` de cada `league_matches`. Estos tests
verifican que el renombrado:

- Actualiza ambos sitios en una sola transacción (o todo o nada).
- En torneos solo toca coincidencias EXACTAS: placeholders "Ganador
  Partido N", BYEs e `is_placeholder` quedan intactos.
- Se integra con standings (el nombre nuevo hereda las estadísticas) y con
  `record_result`/`propagate_winner` (propaga el nombre nuevo).

No toca Supabase. Usa SQLite en memoria + mock de rx.session().
"""

from __future__ import annotations

import json

import pytest
from sqlmodel import select

from TennisTournament.models.league import League
from TennisTournament.models.league_match import LeagueMatch
from TennisTournament.models.tournament import Tournament
from TennisTournament.states.league_state import LeagueState

pytestmark = pytest.mark.integration


def _make_state() -> LeagueState:
    return LeagueState(_reflex_internal_init=True)


def _league_matches(session, comp_id: int, comp_type: str) -> list[LeagueMatch]:
    field = (
        LeagueMatch.league_id if comp_type == "league" else LeagueMatch.tournament_id
    )
    return session.exec(select(LeagueMatch).where(field == comp_id)).all()


class TestRenameEnLiga:
    def _setup_league(self, state) -> int:
        state.setup_league("Liga", ["Alice", "Bob", "Carol"])
        return state.active_competition_id

    def test_actualiza_players_json_y_todos_los_partidos(
        self, mock_rx_session
    ):
        session = mock_rx_session
        state = _make_state()
        league_id = self._setup_league(state)

        error = state.rename_player(league_id, "league", "Alice", "Alicia")

        assert error is None
        league = session.get(League, league_id)
        assert json.loads(league.players_json) == ["Alicia", "Bob", "Carol"]
        matches = _league_matches(session, league_id, "league")
        assert all("Alice" not in (m.home, m.away) for m in matches)
        # Round Robin x2 de 3 jugadores: Alicia juega ida+vuelta vs cada rival.
        appearances = sum(
            1 for m in matches if "Alicia" in (m.home, m.away)
        )
        assert appearances == 4

    def test_standings_conservan_estadisticas_con_nombre_nuevo(
        self, mock_rx_session
    ):
        state = _make_state()
        league_id = self._setup_league(state)

        # Finalizar un partido donde juega Alice (2-0).
        matches = state.competitions[0].matches
        target = next(m for m in matches if "Alice" in (m.home, m.away))
        alice_is_home = target.home == "Alice"
        state.record_result(
            target.id,
            sets_home=2 if alice_is_home else 0,
            sets_away=0 if alice_is_home else 2,
        )

        error = state.rename_player(league_id, "league", "Alice", "Alicia")
        assert error is None

        rows = {r["player"]: r for r in state.standings}
        assert "Alice" not in rows
        assert rows["Alicia"]["pg"] == "1"
        assert rows["Alicia"]["pts"] == "3"

    def test_duplicado_no_cambia_nada(self, mock_rx_session):
        session = mock_rx_session
        state = _make_state()
        league_id = self._setup_league(state)

        error = state.rename_player(league_id, "league", "Alice", "bob")

        assert error is not None
        league = session.get(League, league_id)
        assert json.loads(league.players_json) == ["Alice", "Bob", "Carol"]
        matches = _league_matches(session, league_id, "league")
        assert any("Alice" in (m.home, m.away) for m in matches)

    def test_competicion_inexistente(self, mock_rx_session):
        state = _make_state()
        error = state.rename_player(9999, "league", "Alice", "Alicia")
        assert error is not None

    def test_rename_y_record_result_posterior_propagan_nombre_nuevo(
        self, mock_rx_session
    ):
        """Renombrar y luego finalizar un partido usa el nombre nuevo."""
        state = _make_state()
        league_id = self._setup_league(state)
        state.rename_player(league_id, "league", "Alice", "Alicia")

        matches = state.competitions[0].matches
        target = next(m for m in matches if "Alicia" in (m.home, m.away))
        alicia_is_home = target.home == "Alicia"
        state.record_result(
            target.id,
            sets_home=2 if alicia_is_home else 0,
            sets_away=0 if alicia_is_home else 2,
        )

        rows = {r["player"]: r for r in state.standings}
        assert rows["Alicia"]["pg"] == "1"


class TestRenameEnTorneo:
    def _setup_tournament(self, state, players: list[str]) -> int:
        state.setup_tournament("Torneo", players)
        return state.active_competition_id

    def test_placeholders_y_byes_intactos(self, mock_rx_session):
        """Torneo de 5: hay BYEs y placeholders 'Ganador Partido N' que el
        renombrado no debe tocar aunque renombremos a todos los reales."""
        session = mock_rx_session
        state = _make_state()
        tid = self._setup_tournament(
            state, ["Alice", "Bob", "Carol", "Dave", "Eve"]
        )

        before = _league_matches(session, tid, "tournament")
        placeholders_before = sorted(
            n
            for m in before
            for n in (m.home, m.away)
            if n.startswith("Ganador Partido") or n == "BYE"
        )
        flags_before = {m.id: m.is_placeholder for m in before}

        for old, new in [("Alice", "Alicia"), ("Bob", "Roberto")]:
            assert state.rename_player(tid, "tournament", old, new) is None

        after = _league_matches(session, tid, "tournament")
        placeholders_after = sorted(
            n
            for m in after
            for n in (m.home, m.away)
            if n.startswith("Ganador Partido") or n == "BYE"
        )
        assert placeholders_after == placeholders_before
        assert {m.id: m.is_placeholder for m in after} == flags_before
        assert all("Alice" not in (m.home, m.away) for m in after)
        assert all("Bob" not in (m.home, m.away) for m in after)

    def test_renombrar_jugador_ya_avanzado_actualiza_rondas_posteriores(
        self, mock_rx_session
    ):
        """Con 4 jugadores: gana una semifinal, avanza a la final, y al
        renombrarlo su slot en la final también se actualiza."""
        session = mock_rx_session
        state = _make_state()
        tid = self._setup_tournament(state, ["Alice", "Bob", "Carol", "Dave"])

        # Finalizar la primera semifinal: gana el home.
        semis = [
            m
            for m in state.competitions[0].matches
            if m.round_num == 1
        ]
        first = semis[0]
        winner = first.home
        state.record_result(first.id, sets_home=2, sets_away=0)

        # El ganador aparece ahora en la final (ronda 2).
        final_row = next(
            m
            for m in _league_matches(session, tid, "tournament")
            if m.round_num == 2
        )
        assert winner in (final_row.home, final_row.away)

        error = state.rename_player(tid, "tournament", winner, "Campeona")
        assert error is None

        session.refresh(final_row)
        assert "Campeona" in (final_row.home, final_row.away)
        assert winner not in (final_row.home, final_row.away)
        assert json.loads(
            session.get(Tournament, tid).players_json
        ).count("Campeona") == 1
