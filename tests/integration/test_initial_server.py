"""Tests de integración del sacador inicial (Funcionalidad "¿Quién saca?").

Cubren:
- `resolve_initial_server`: matriz de decisión al cargar un partido
  (elección persistida / partido con progreso / partido virgen).
- `ScoreboardState.choose_server`: fija server_id, marca la elección y la
  persiste en la fila `league_matches` cuando el partido es de competición.
- `show_server_modal`: sólo visible con partido cargado, en curso y sin
  sacador elegido.

No toca Supabase. Usa SQLite en memoria + mock de rx.session().
"""

from __future__ import annotations

import pytest

from TennisTournament.logic.serving import resolve_initial_server
from TennisTournament.models.league_match import LeagueMatch
from TennisTournament.states.scoreboard_state import ScoreboardState

pytestmark = pytest.mark.integration


def _make_state(**overrides) -> ScoreboardState:
    s = ScoreboardState(_reflex_internal_init=True)
    for key, value in overrides.items():
        setattr(s, key, value)
    return s


def _seed_match(session, **overrides) -> LeagueMatch:
    defaults = dict(
        league_id=None,
        tournament_id=None,
        round_num=1,
        leg=1,
        home="Alice",
        away="Bob",
        status="Pendiente",
    )
    defaults.update(overrides)
    m = LeagueMatch(**defaults)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


# =============================================================================
# 1. Matriz de decisión al cargar un partido
# =============================================================================


class TestResolveInitialServer:
    @pytest.mark.parametrize("persisted", [1, 2])
    def test_eleccion_persistida_se_recupera_sin_preguntar(self, persisted):
        server_id, chosen = resolve_initial_server(
            persisted, "Pendiente", 0, 0
        )
        assert server_id == persisted
        assert chosen is True

    def test_partido_virgen_pregunta(self):
        server_id, chosen = resolve_initial_server(None, "Pendiente", 0, 0)
        assert server_id == 1
        assert chosen is False

    def test_partido_finalizado_no_pregunta(self):
        _, chosen = resolve_initial_server(None, "Finalizado", 2, 0)
        assert chosen is True

    def test_partido_con_sets_acumulados_no_pregunta(self):
        _, chosen = resolve_initial_server(None, "Pendiente", 1, 0)
        assert chosen is True

    @pytest.mark.parametrize("invalid", [0, 3, -1])
    def test_valor_persistido_invalido_se_ignora(self, invalid):
        server_id, chosen = resolve_initial_server(
            invalid, "Pendiente", 0, 0
        )
        assert server_id == 1
        assert chosen is False


# =============================================================================
# 2. choose_server: estado + persistencia
# =============================================================================


class TestChooseServer:
    def test_persiste_en_partido_de_competicion(self, mock_rx_session):
        session = mock_rx_session
        match = _seed_match(session)
        state = _make_state(
            player_j1="Alice", player_j2="Bob", league_match_id=match.id
        )

        state.choose_server(2)

        assert state.server_id == 2
        assert state.server_chosen is True
        session.refresh(match)
        assert match.initial_server == 2

    def test_casual_no_toca_db(self, mock_rx_session):
        session = mock_rx_session
        other = _seed_match(session)  # fila ajena que no debe cambiar
        state = _make_state(
            player_j1="Alice", player_j2="Bob", is_casual=True
        )

        state.choose_server(1)

        assert state.server_id == 1
        assert state.server_chosen is True
        session.refresh(other)
        assert other.initial_server is None

    @pytest.mark.parametrize("invalid", [0, 3, -1])
    def test_id_invalido_se_ignora(self, mock_rx_session, invalid):
        state = _make_state(player_j1="Alice", player_j2="Bob")

        state.choose_server(invalid)

        assert state.server_chosen is False
        assert state.server_id == 1

    def test_no_permite_reelegir(self, mock_rx_session):
        session = mock_rx_session
        match = _seed_match(session)
        state = _make_state(
            player_j1="Alice", player_j2="Bob", league_match_id=match.id
        )

        state.choose_server(2)
        state.choose_server(1)  # segunda elección: ignorada

        assert state.server_id == 2
        session.refresh(match)
        assert match.initial_server == 2

    def test_rotacion_posterior_respeta_la_eleccion(self, mock_rx_session):
        """Tras elegir a J2, cerrar un juego rota el saque a J1."""
        state = _make_state(
            player_j1="Alice", player_j2="Bob", is_casual=True
        )
        state.choose_server(2)

        # 4 puntos limpios de Alice cierran el primer juego (15-30-40-juego).
        for _ in range(4):
            state.sumar_punto(1)

        assert state.juegos_j1 == 1
        assert state.server_id == 1  # rotó desde el 2 elegido

    def test_undo_hasta_cero_no_reabre_modal(self, mock_rx_session):
        """`server_chosen` queda fuera de la pila de undo a propósito."""
        state = _make_state(
            player_j1="Alice", player_j2="Bob", is_casual=True
        )
        state.choose_server(2)
        state.sumar_punto(1)
        state.undo_point()

        assert state.puntos_j1 == 0
        assert state.server_chosen is True
        assert state.show_server_modal is False


# =============================================================================
# 3. show_server_modal
# =============================================================================


class TestShowServerModal:
    def test_visible_con_partido_cargado_sin_eleccion(self):
        state = _make_state(player_j1="Alice", player_j2="Bob")
        assert state.show_server_modal is True

    def test_oculto_sin_partido_cargado(self):
        state = _make_state()  # /scoreboard sin params: nombres vacíos
        assert state.show_server_modal is False

    def test_oculto_tras_elegir(self):
        state = _make_state(
            player_j1="Alice", player_j2="Bob", server_chosen=True
        )
        assert state.show_server_modal is False

    def test_oculto_en_partido_finalizado(self):
        from TennisTournament.models.match import ESTADO_FINALIZADO

        state = _make_state(
            player_j1="Alice", player_j2="Bob", estado=ESTADO_FINALIZADO
        )
        assert state.show_server_modal is False

    def test_reset_match_vuelve_a_preguntar(self):
        state = _make_state(
            player_j1="Alice", player_j2="Bob", server_chosen=True
        )
        state.reset_match()
        assert state.show_server_modal is True
