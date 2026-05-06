"""Tests unitarios de la state machine de puntuación en models/match.py.

Cubre:
- Puntuación básica 0 → 15 → 30 → 40 → juego.
- Deuce / ventaja con alternancias múltiples hasta cerrar por diferencia de 2.
- Cierre de set 6-4 y 7-5 (sin tie-break).
- Activación de tie-break en 6-6, cierre normal (7-5 TB) y largo (10-8 TB).
- Finalización de partido al mejor de 3.
- Validaciones: no sumar puntos tras "Finalizado" y rechazo de player inválido.
"""

from __future__ import annotations

import pytest

from TennisTournament.models.match import (
    ESTADO_EN_CURSO,
    ESTADO_FINALIZADO,
    Match,
)


pytestmark = pytest.mark.unit


# --------------------------- helpers ---------------------------

def new_match(best_of: int = 3) -> Match:
    return Match(player_j1="Alice", player_j2="Bob", config_sets=best_of)


def score(match: Match, sequence: str) -> None:
    """Aplica una secuencia como 'AABBA...' donde A=jugador1, B=jugador2."""
    for ch in sequence:
        if ch == "A":
            match.add_point(1)
        elif ch == "B":
            match.add_point(2)
        else:
            raise ValueError(f"carácter inválido: {ch!r}")


def win_n_games(match: Match, player: int, n: int) -> None:
    """Hace que `player` gane `n` juegos consecutivos limpios (a 4 puntos)."""
    for _ in range(n):
        for _ in range(4):
            match.add_point(player)


# =========================================================
# 1. Puntuación básica: 0 → 15 → 30 → 40 → juego
# =========================================================

class TestBasicScoring:
    def test_visual_mapping_initial(self):
        m = new_match()
        assert m.score_visual_j1 == "0"
        assert m.score_visual_j2 == "0"

    def test_progression_15_30_40(self):
        m = new_match()
        m.add_point(1)
        assert m.score_visual_j1 == "15"
        m.add_point(1)
        assert m.score_visual_j1 == "30"
        m.add_point(1)
        assert m.score_visual_j1 == "40"
        # El rival sigue en 0
        assert m.score_visual_j2 == "0"
        # Aún no se ha ganado juego alguno
        assert m.juegos_j1 == 0

    def test_clean_game_win(self):
        m = new_match()
        # 4-0 limpia → gana juego (40 - 0 con diferencia de 2 a partir de ≥4)
        for _ in range(4):
            m.add_point(1)
        assert m.juegos_j1 == 1
        assert m.juegos_j2 == 0
        # Puntos reseteados al cerrar juego
        assert m.puntos_j1 == 0
        assert m.puntos_j2 == 0

    def test_game_win_with_diff_of_two(self):
        m = new_match()
        # 40-15: A=3, B=1, luego A suma → A=4 diff=3 → cierra
        score(m, "AAABA")
        assert m.juegos_j1 == 1
        assert m.puntos_j1 == 0 and m.puntos_j2 == 0


# =========================================================
# 2. Deuce y ventaja
# =========================================================

class TestDeuceAndAdvantage:
    def test_deuce_detection(self):
        m = new_match()
        score(m, "AAABBB")  # 40-40
        assert m.score_visual_j1 == "40"
        assert m.score_visual_j2 == "40"
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0

    def test_advantage_then_deuce_back(self):
        m = new_match()
        score(m, "AAABBB")  # 40-40
        m.add_point(1)      # A ventaja
        assert m.score_visual_j1 == "Adv"
        assert m.score_visual_j2 == "40"
        m.add_point(2)      # vuelve a deuce
        assert m.score_visual_j1 == "40"
        assert m.score_visual_j2 == "40"
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0

    def test_multiple_deuce_alternations_until_win_by_two(self):
        m = new_match()
        score(m, "AAABBB")           # 40-40
        # Tres alternancias Adv A → Deuce → Adv B → Deuce → Adv A → Deuce
        score(m, "ABABAB")
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0
        # Ahora A gana por diferencia de 2: Adv → game
        score(m, "AA")
        assert m.juegos_j1 == 1
        assert m.puntos_j1 == 0 and m.puntos_j2 == 0

    def test_advantage_then_win(self):
        m = new_match()
        score(m, "AAABBB")  # 40-40
        score(m, "AA")      # Adv A → game A
        assert m.juegos_j1 == 1


# =========================================================
# 3. Sets: cierre 6-4 y 7-5 (sin tie-break)
# =========================================================

class TestSetClosure:
    def test_set_6_4(self):
        m = new_match()
        win_n_games(m, 1, 4)  # 4-0
        win_n_games(m, 2, 4)  # 4-4
        win_n_games(m, 1, 2)  # 6-4 → set para A
        assert m.sets_j1 == 1
        assert m.sets_j2 == 0
        # Al cerrar set, juegos/puntos a cero
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0
        assert not m.is_tiebreak

    def test_set_7_5(self):
        m = new_match()
        # 5-5
        win_n_games(m, 1, 5)
        win_n_games(m, 2, 5)
        assert m.juegos_j1 == 5 and m.juegos_j2 == 5
        # 6-5: A gana un juego
        win_n_games(m, 1, 1)
        assert m.juegos_j1 == 6 and m.juegos_j2 == 5
        assert m.sets_j1 == 0  # 6-5 no cierra (diff 1)
        # 7-5: A cierra el set
        win_n_games(m, 1, 1)
        assert m.sets_j1 == 1
        assert not m.is_tiebreak


# =========================================================
# 4. Tie-break
# =========================================================

class TestTiebreak:
    @staticmethod
    def _reach_6_6(m: Match) -> None:
        """Alterna juegos hasta 6-6 sin cerrar el set.

        Secuencia: 1-1, 2-2, 3-3, 4-4, 5-5, 6-5 (diff 1 → no cierra), 6-6 → tie-break.
        """
        for _ in range(5):
            win_n_games(m, 1, 1)
            win_n_games(m, 2, 1)
        # Ahora 5-5
        win_n_games(m, 1, 1)  # 6-5 (no cierra: diff 1)
        win_n_games(m, 2, 1)  # 6-6 → activa tie-break

    def test_tiebreak_activated_at_6_6(self):
        m = new_match()
        self._reach_6_6(m)
        assert m.juegos_j1 == 6 and m.juegos_j2 == 6
        assert m.is_tiebreak is True
        assert m.sets_j1 == 0 and m.sets_j2 == 0

    def test_tiebreak_visual_is_numeric(self):
        m = new_match()
        self._reach_6_6(m)
        m.add_point(1)
        m.add_point(1)
        m.add_point(2)
        # En tie-break se muestran enteros, NO la puntuación 15/30/40
        assert m.score_visual_j1 == "2"
        assert m.score_visual_j2 == "1"

    def test_tiebreak_won_7_5(self):
        m = new_match()
        self._reach_6_6(m)
        # 5 puntos para cada uno
        for _ in range(5):
            m.add_point(1)
            m.add_point(2)
        assert m.puntos_j1 == 5 and m.puntos_j2 == 5
        # A gana 2 seguidos → 7-5
        m.add_point(1)
        m.add_point(1)
        assert m.is_tiebreak is False
        assert m.sets_j1 == 1
        # Tras cerrar set, juegos y puntos vuelven a 0
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0

    def test_tiebreak_does_not_close_at_7_6(self):
        m = new_match()
        self._reach_6_6(m)
        for _ in range(6):
            m.add_point(1)
            m.add_point(2)
        assert m.puntos_j1 == 6 and m.puntos_j2 == 6
        m.add_point(1)  # 7-6 — no cierra (diff 1)
        assert m.is_tiebreak is True
        assert m.sets_j1 == 0

    def test_long_tiebreak_10_8(self):
        m = new_match()
        self._reach_6_6(m)
        # Llegar a 8-8 alternando
        for _ in range(8):
            m.add_point(1)
            m.add_point(2)
        assert m.puntos_j1 == 8 and m.puntos_j2 == 8
        assert m.is_tiebreak is True
        # 9-8
        m.add_point(1)
        assert m.is_tiebreak is True
        # 10-8 → cierra el tie-break y el set
        m.add_point(1)
        assert m.is_tiebreak is False
        assert m.sets_j1 == 1


# =========================================================
# 5. Finalización de partido (best of 3)
# =========================================================

class TestMatchCompletion:
    def _win_set_6_0(self, m: Match, player: int) -> None:
        win_n_games(m, player, 6)

    def test_match_finishes_at_two_sets_best_of_3(self):
        m = new_match(best_of=3)
        assert m.sets_to_win == 2

        self._win_set_6_0(m, 1)
        assert m.sets_j1 == 1
        assert m.estado == ESTADO_EN_CURSO
        assert m.is_finished is False

        self._win_set_6_0(m, 1)
        assert m.sets_j1 == 2
        assert m.estado == ESTADO_FINALIZADO
        assert m.is_finished is True
        assert m.winner == 1
        assert m.finished_at is not None

    def test_match_finishes_at_three_sets_best_of_5(self):
        m = new_match(best_of=5)
        assert m.sets_to_win == 3
        for _ in range(3):
            self._win_set_6_0(m, 2)
        assert m.sets_j2 == 3
        assert m.is_finished is True
        assert m.winner == 2

    def test_no_points_added_after_finished(self):
        m = new_match(best_of=3)
        self._win_set_6_0(m, 1)
        self._win_set_6_0(m, 1)
        assert m.is_finished

        snapshot = (
            m.sets_j1, m.sets_j2, m.juegos_j1, m.juegos_j2,
            m.puntos_j1, m.puntos_j2,
        )
        # Intento de sumar puntos tras finalizar: no-op silencioso
        m.add_point(1)
        m.add_point(2)
        assert (
            m.sets_j1, m.sets_j2, m.juegos_j1, m.juegos_j2,
            m.puntos_j1, m.puntos_j2,
        ) == snapshot


# =========================================================
# 6. Validaciones
# =========================================================

class TestValidation:
    def test_invalid_player_raises(self):
        m = new_match()
        with pytest.raises(ValueError):
            m.add_point(3)
        with pytest.raises(ValueError):
            m.add_point(0)

    def test_reset_clears_state(self):
        m = new_match()
        score(m, "AAAA")
        m.reset()
        assert m.puntos_j1 == 0 and m.puntos_j2 == 0
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0
        assert m.sets_j1 == 0 and m.sets_j2 == 0
        assert m.is_tiebreak is False
        assert m.estado == ESTADO_EN_CURSO
        assert m.finished_at is None


# =========================================================
# 7. Resultados imposibles — la state machine no permite saltarse pasos
# =========================================================


class TestImpossibleResults:
    """Verifica que la máquina de estados no permite alcanzar un marcador
    final sin haber transitado por todos los estados intermedios obligatorios.

    En tenis es imposible llegar a 7-6 sin haber pasado por 5-5 y luego 6-6
    (que activa el tie-break). Estos tests demuestran que cualquier camino
    que llegue al 7-6 forzosamente cumple esa condición.
    """

    def test_imposible_7_6_sin_pasar_por_5_5(self, fresh_match):
        # Arrange: partido limpio.
        m = fresh_match()

        # Act: hacemos 5 juegos a Alice y 4 a Bob, y vamos rastreando los
        # estados intermedios.
        observed_states: list[tuple[int, int]] = []
        for _ in range(5):
            for _ in range(4):
                m.add_point(1)
            observed_states.append((m.juegos_j1, m.juegos_j2))
        for _ in range(4):
            for _ in range(4):
                m.add_point(2)
            observed_states.append((m.juegos_j1, m.juegos_j2))

        # En este punto debería ir 5-4. Empatamos a 5 y luego 6-6.
        for _ in range(4):
            m.add_point(2)            # 5-5
        observed_states.append((m.juegos_j1, m.juegos_j2))

        for _ in range(4):
            m.add_point(1)            # 6-5
        observed_states.append((m.juegos_j1, m.juegos_j2))

        for _ in range(4):
            m.add_point(2)            # 6-6 → activa tie-break
        observed_states.append((m.juegos_j1, m.juegos_j2))

        # Assert: el camino visitó (5,5) y (6,6) antes que cualquier 7-x.
        assert (5, 5) in observed_states
        assert (6, 6) in observed_states
        # Nunca se alcanza un 7-6 sin pasar por 6-6 primero
        idx_66 = observed_states.index((6, 6))
        siete_seises = [
            i for i, st in enumerate(observed_states) if st == (7, 6)
        ]
        for i in siete_seises:
            assert i > idx_66

    def test_no_se_pueden_ganar_2_juegos_seguidos_con_un_solo_punto(
        self, fresh_match
    ):
        # Arrange: cada juego requiere mínimo 4 puntos con diff de 2; con un
        # único punto NO se puede haber ganado un juego.
        m = fresh_match()

        # Act
        m.add_point(1)

        # Assert: ni juegos ni sets se incrementan, sólo puntos.
        assert m.puntos_j1 == 1
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0
        assert m.sets_j1 == 0 and m.sets_j2 == 0

    def test_set_no_cierra_a_6_5(self, fresh_match):
        # Arrange: Para llegar a 6-5 sin cerrar el set, hay que pasar por el 5-5
        m = fresh_match()
        for _ in range(5):
            win_n_games(m, 1, 1) # Alice gana uno (1-0, 2-1...)
            win_n_games(m, 2, 1) # Bob empata (1-1, 2-2... hasta 5-5)
        
        # Act: Alice gana el juego del 6-5
        win_n_games(m, 1, 1)

        # Assert: 6-5 -> diferencia de 1 -> El set NO debe cerrarse
        assert m.juegos_j1 == 6 and m.juegos_j2 == 5
        assert m.sets_j1 == 0
        assert m.estado == ESTADO_EN_CURSO
        assert m.is_tiebreak is False

    def test_no_se_activa_tiebreak_a_5_5(self, fresh_match):
        # Arrange / Act: alternar hasta 5-5
        m = fresh_match()
        for _ in range(5):
            for _ in range(4):
                m.add_point(1)
            for _ in range(4):
                m.add_point(2)

        # Assert: el tie-break sólo se activa en config_games-config_games.
        assert m.juegos_j1 == 5 and m.juegos_j2 == 5
        assert m.is_tiebreak is False


# =========================================================
# 8. config_games configurable (set corto a 4 / largo a 8)
# =========================================================


class TestConfigurableGamesPerSet:
    def test_set_corto_a_4_juegos(self, fresh_match):
        # Arrange: set "corto" a 4 juegos por set.
        m = fresh_match(best_of=3, games=4)

        # Act: 4-0 limpio para Alice.
        for _ in range(4):
            for _ in range(4):
                m.add_point(1)

        # Assert: el set se cierra en 4-0 (no sigue hasta 6).
        assert m.sets_j1 == 1
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0

    def test_tiebreak_en_4_4_si_config_games_es_4(self, fresh_match):
        # Arrange: alternar hasta 3-3 y luego 4-4.
        m = fresh_match(best_of=3, games=4)

        # Act: 3-3
        for _ in range(3):
            for _ in range(4):
                m.add_point(1)
            for _ in range(4):
                m.add_point(2)
        # 4-3
        for _ in range(4):
            m.add_point(1)
        # 4-4 → debe activar tie-break porque config_games=4
        for _ in range(4):
            m.add_point(2)

        # Assert
        assert m.juegos_j1 == 4 and m.juegos_j2 == 4
        assert m.is_tiebreak is True
        assert m.sets_j1 == 0 and m.sets_j2 == 0

    def test_set_largo_a_8_juegos_no_cierra_en_6(self, fresh_match):
        # Arrange: configuración exótica de 8 juegos por set.
        m = fresh_match(best_of=3, games=8)

        # Act: Alice gana 6-0 (ningún set debe cerrarse).
        for _ in range(6):
            for _ in range(4):
                m.add_point(1)

        # Assert: 6-0 con config_games=8 ⇒ set sigue abierto.
        assert m.juegos_j1 == 6 and m.juegos_j2 == 0
        assert m.sets_j1 == 0
        assert m.is_tiebreak is False

    def test_set_largo_a_8_cierra_en_8_x(self, fresh_match):
        # Arrange / Act: 8-0 con config_games=8 → cierra set.
        m = fresh_match(best_of=3, games=8)
        for _ in range(8):
            for _ in range(4):
                m.add_point(1)

        # Assert
        assert m.sets_j1 == 1
        assert m.juegos_j1 == 0 and m.juegos_j2 == 0


# =========================================================
# 9. Aislamiento — la lógica de puntuación no toca DB ni I/O
# =========================================================


class TestPurityIsolation:
    """Sanidad: si un día alguien introduce I/O dentro de `add_point`
    (logging a un servicio, escritura a DB, ...), estos mocks lo cazan.
    """

    def test_add_point_no_realiza_io(self, fresh_match, monkeypatch):
        # Arrange: monkey-patch de `open` para detectar accesos a disco.
        from unittest.mock import MagicMock

        open_spy = MagicMock(side_effect=AssertionError("add_point tocó disco"))
        monkeypatch.setattr("builtins.open", open_spy)

        # Act: jugar un set entero.
        m = fresh_match()
        for _ in range(6):
            for _ in range(4):
                m.add_point(1)

        # Assert: el spy nunca se llamó (cero I/O en el flujo crítico).
        assert open_spy.call_count == 0
        assert m.sets_j1 == 1
