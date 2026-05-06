"""Tests unitarios de `TennisTournament/logic/fixtures.py`.

Verifica el agrupamiento de partidos por ronda con pareo ida[i] ↔ vuelta[i].
"""

from __future__ import annotations

import pytest

from TennisTournament.logic.fixtures import (
    STATUS_FINALIZADO,
    FixtureMatch,
    FixturePairView,
    RoundFixtures,
    group_fixtures,
)


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make(
    id_: int,
    round_num: int,
    leg: int,
    home: str,
    away: str,
    status: str = "Pendiente",
    sh: int = 0,
    sa: int = 0,
) -> FixtureMatch:
    return FixtureMatch(
        id=id_,
        round_num=round_num,
        leg=leg,
        home=home,
        away=away,
        status=status,
        sets_home=sh,
        sets_away=sa,
    )


# =============================================================================
# 1. Casos vacíos
# =============================================================================


class TestEmpty:
    def test_lista_vacia_devuelve_vacio(self):
        # Arrange / Act
        result = group_fixtures([])
        # Assert
        assert result == []


# =============================================================================
# 2. Estructura de salida y agrupamiento por ronda
# =============================================================================


class TestGrouping:
    def test_una_ronda_con_ida_y_vuelta(self):
        # Arrange: 2 partidos de ronda 1 → ida[0] y vuelta[0] del mismo enfrentamiento.
        matches = [
            make(1, round_num=1, leg=1, home="Alice", away="Bob"),
            make(2, round_num=1, leg=2, home="Bob", away="Alice"),
        ]

        # Act
        result = group_fixtures(matches)

        # Assert
        assert len(result) == 1
        ronda = result[0]
        assert isinstance(ronda, RoundFixtures)
        assert ronda.round_num == 1
        assert ronda.label == "Ronda 1"
        assert len(ronda.pairs) == 1

        pair = ronda.pairs[0]
        assert isinstance(pair, FixturePairView)
        assert pair.ida is not None and pair.vuelta is not None
        assert pair.ida.match_id == 1
        assert pair.ida.home == "Alice" and pair.ida.away == "Bob"
        assert pair.vuelta.match_id == 2
        assert pair.vuelta.home == "Bob" and pair.vuelta.away == "Alice"

    def test_multiples_rondas_orden_ascendente(self):
        # Arrange: rondas 1, 2 y 3 desordenadas.
        matches = [
            make(10, round_num=2, leg=1, home="A", away="B"),
            make(20, round_num=3, leg=1, home="C", away="D"),
            make(30, round_num=1, leg=1, home="E", away="F"),
        ]

        # Act
        result = group_fixtures(matches)

        # Assert: las rondas vienen ordenadas 1, 2, 3.
        assert [r.round_num for r in result] == [1, 2, 3]
        assert [r.label for r in result] == ["Ronda 1", "Ronda 2", "Ronda 3"]

    def test_pareo_ida_vuelta_por_indice_de_insercion(self):
        # Arrange: 2 enfrentamientos (4 partidos) en la misma ronda.
        # Orden de inserción: idaA, idaB, vueltaA, vueltaB.
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob"),
            make(2, 1, leg=1, home="Carol", away="Dave"),
            make(3, 1, leg=2, home="Bob", away="Alice"),
            make(4, 1, leg=2, home="Dave", away="Carol"),
        ]

        # Act
        result = group_fixtures(matches)
        pairs = result[0].pairs

        # Assert: par 0 = (1, 3); par 1 = (2, 4).
        assert len(pairs) == 2
        assert pairs[0].ida.match_id == 1 and pairs[0].vuelta.match_id == 3
        assert pairs[1].ida.match_id == 2 and pairs[1].vuelta.match_id == 4


# =============================================================================
# 3. Flags de ganador (home_winner / away_winner)
# =============================================================================


class TestWinnerFlags:
    def test_home_winner_solo_si_finalizado_y_sets_mayores(self):
        # Arrange: partido finalizado 2-1 a favor del local.
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob",
                 status=STATUS_FINALIZADO, sh=2, sa=1),
        ]

        # Act
        leg = group_fixtures(matches)[0].pairs[0].ida

        # Assert
        assert leg.home_winner is True
        assert leg.away_winner is False

    def test_away_winner_cuando_visitante_gana(self):
        # Arrange
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob",
                 status=STATUS_FINALIZADO, sh=0, sa=2),
        ]
        # Act
        leg = group_fixtures(matches)[0].pairs[0].ida
        # Assert
        assert leg.away_winner is True
        assert leg.home_winner is False

    def test_pendiente_sin_ganador_aunque_haya_sets(self):
        # Arrange: status pendiente con sets parciales (no debería decidir).
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob",
                 status="Pendiente", sh=2, sa=0),
        ]
        # Act
        leg = group_fixtures(matches)[0].pairs[0].ida
        # Assert: no se considera ganador hasta que esté finalizado.
        assert leg.home_winner is False
        assert leg.away_winner is False


# =============================================================================
# 4. Asimetría ida/vuelta (defensa)
# =============================================================================


class TestAsymmetry:
    def test_mas_idas_que_vueltas_rellena_con_none(self):
        # Arrange: 2 idas, 1 vuelta (escenario degradado).
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob"),
            make(2, 1, leg=1, home="Carol", away="Dave"),
            make(3, 1, leg=2, home="Bob", away="Alice"),
        ]

        # Act
        pairs = group_fixtures(matches)[0].pairs

        # Assert: 2 pares; el segundo tiene vuelta = None.
        assert len(pairs) == 2
        assert pairs[0].vuelta is not None
        assert pairs[1].vuelta is None
        assert pairs[1].ida is not None and pairs[1].ida.match_id == 2

    def test_mas_vueltas_que_idas(self):
        # Arrange: 1 ida, 2 vueltas.
        matches = [
            make(1, 1, leg=1, home="Alice", away="Bob"),
            make(2, 1, leg=2, home="Bob", away="Alice"),
            make(3, 1, leg=2, home="Dave", away="Carol"),
        ]

        # Act
        pairs = group_fixtures(matches)[0].pairs

        # Assert: 2 pares; en el segundo no hay ida.
        assert len(pairs) == 2
        assert pairs[1].ida is None
        assert pairs[1].vuelta is not None and pairs[1].vuelta.match_id == 3
