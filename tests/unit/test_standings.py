"""Tests unitarios de `TennisTournament/logic/standings.py`.

Cubre el cálculo de clasificación con todos los criterios de desempate:
  1. Puntos (3 por victoria).
  2. Diferencia de sets (sets_won − sets_lost).
  3. Orden alfabético del nombre.

Patrón AAA explícito en cada test.
"""

from __future__ import annotations

import pytest

from TennisTournament.logic.standings import (
    STATUS_FINALIZADO,
    MatchResult,
    StandingsRow,
    compute_standings,
)


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def finished(home: str, away: str, sh: int, sa: int) -> MatchResult:
    return MatchResult(home=home, away=away, sets_home=sh, sets_away=sa,
                       status=STATUS_FINALIZADO)


def pending(home: str, away: str) -> MatchResult:
    return MatchResult(home=home, away=away, sets_home=0, sets_away=0,
                       status="Pendiente")


# =============================================================================
# 1. Casos básicos
# =============================================================================


class TestStandingsBasic:
    def test_sin_jugadores_devuelve_vacio(self):
        # Arrange / Act
        result = compute_standings(players=[], matches=[])
        # Assert
        assert result == []

    def test_sin_partidos_todos_a_cero(self, players_4):
        # Arrange / Act
        result = compute_standings(players_4, matches=[])

        # Assert: todos a 0; orden alfabético al estar empatados.
        assert len(result) == 4
        assert all(isinstance(r, StandingsRow) for r in result)
        assert [r.player for r in result] == sorted(players_4)
        for r in result:
            assert r.pj == 0 and r.pg == 0 and r.pp == 0
            assert r.pts == 0
            assert r.sets_won == 0 and r.sets_lost == 0

    def test_victoria_otorga_3_puntos(self, players_4):
        # Arrange: Alice gana a Bob por 2-0.
        matches = [finished("Alice", "Bob", 2, 0)]

        # Act
        result = compute_standings(players_4, matches)

        # Assert: Alice 3pts, Bob 0pts, ambos con PJ=1.
        by_name = {r.player: r for r in result}
        assert by_name["Alice"].pts == 3
        assert by_name["Alice"].pg == 1 and by_name["Alice"].pp == 0
        assert by_name["Bob"].pts == 0
        assert by_name["Bob"].pg == 0 and by_name["Bob"].pp == 1
        assert by_name["Alice"].pj == 1 and by_name["Bob"].pj == 1
        # Sets ganados/perdidos correctamente reflejados
        assert by_name["Alice"].sets_won == 2 and by_name["Alice"].sets_lost == 0
        assert by_name["Bob"].sets_won == 0 and by_name["Bob"].sets_lost == 2


# =============================================================================
# 2. Filtrado de partidos no aplicables
# =============================================================================


class TestFiltering:
    def test_partidos_pendientes_se_ignoran(self, players_4):
        # Arrange: hay un finalizado y un pendiente.
        matches = [
            finished("Alice", "Bob", 2, 0),
            pending("Carol", "Dave"),
        ]

        # Act
        result = compute_standings(players_4, matches)
        by_name = {r.player: r for r in result}

        # Assert: Carol y Dave no han sumado PJ.
        assert by_name["Carol"].pj == 0
        assert by_name["Dave"].pj == 0

    def test_partidos_con_jugador_desconocido_se_ignoran(self, players_4):
        # Arrange: "Eve" no está en la lista oficial.
        matches = [finished("Eve", "Bob", 2, 0)]

        # Act
        result = compute_standings(players_4, matches)
        by_name = {r.player: r for r in result}

        # Assert: nadie suma; el partido no se contabiliza.
        for name in players_4:
            assert by_name[name].pj == 0
            assert by_name[name].pts == 0


# =============================================================================
# 3. Desempates
# =============================================================================


class TestTiebreakers:
    def test_desempate_por_diferencia_de_sets(self):
        # Arrange: 3 jugadores, todos con 1 victoria (3 pts cada uno).
        # Pero la diferencia de sets debería decidir el orden.
        players = ["Alice", "Bob", "Carol"]
        matches = [
            # Alice gana a Bob 2-0
            finished("Alice", "Bob", 2, 0),
            # Bob gana a Carol 2-1
            finished("Bob", "Carol", 2, 1),
            # Carol gana a Alice 2-0
            finished("Carol", "Alice", 2, 0),
        ]
        # Tras estos partidos: cada uno 1V/1D = 3 pts.
        # Diff sets:
        #   Alice: ganó 2, perdió (0+2)=2 → diff 0
        #   Bob:   ganó (0+2)=2, perdió (2+1)=3 → diff -1
        #   Carol: ganó (1+2)=3, perdió (2+0)=2 → diff +1

        # Act
        result = compute_standings(players, matches)

        # Assert: Carol primera (mejor diff), Alice segunda, Bob última.
        assert [r.player for r in result] == ["Carol", "Alice", "Bob"]
        assert all(r.pts == 3 for r in result)

    def test_desempate_alfabetico_cuando_todo_iguala(self, players_4):
        # Arrange: nadie ha jugado → 0 pts, 0 diff de sets.
        # Act
        result = compute_standings(players_4, matches=[])
        # Assert: orden alfabético estricto.
        assert [r.player for r in result] == ["Alice", "Bob", "Carol", "Dave"]

    def test_puntos_tienen_prioridad_sobre_diff_sets(self):
        # Arrange: Bob tiene mucha diff de sets pero menos puntos.
        players = ["Alice", "Bob"]
        matches = [
            # Alice gana 2-0 → 3pts, +2 diff
            finished("Alice", "Bob", 2, 0),
        ]
        # Act
        result = compute_standings(players, matches)
        # Assert: Alice arriba por puntos.
        assert result[0].player == "Alice"
        assert result[0].pts == 3
        assert result[1].player == "Bob"
        assert result[1].pts == 0

    def test_posicion_es_secuencial_desde_1(self, players_4):
        # Arrange / Act
        result = compute_standings(players_4, [])
        # Assert
        assert [r.pos for r in result] == [1, 2, 3, 4]


# =============================================================================
# 4. Empates dentro de un partido (defensa: tenis no debería empatar)
# =============================================================================


class TestMatchDraw:
    def test_empate_da_un_punto_a_cada_uno(self):
        # Arrange: empate 1-1 (defensivo: el motor de tenis no permite,
        # pero la función contempla el caso para robustez).
        players = ["Alice", "Bob"]
        matches = [MatchResult("Alice", "Bob", 1, 1, status=STATUS_FINALIZADO)]

        # Act
        result = compute_standings(players, matches)
        by_name = {r.player: r for r in result}

        # Assert: 1 punto a cada uno; pj=1 sin pg/pp.
        assert by_name["Alice"].pts == 1
        assert by_name["Bob"].pts == 1
        assert by_name["Alice"].pg == 0 and by_name["Alice"].pp == 0
        assert by_name["Bob"].pg == 0 and by_name["Bob"].pp == 0


# =============================================================================
# 5. Pureza
# =============================================================================


class TestPurity:
    def test_no_muta_lista_de_partidos(self, players_4):
        # Arrange
        original = [finished("Alice", "Bob", 2, 0)]
        snapshot = list(original)

        # Act
        compute_standings(players_4, original)

        # Assert: la entrada no se ha modificado.
        assert original == snapshot
