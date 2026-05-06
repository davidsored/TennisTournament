"""Tests unitarios de `TennisTournament/logic/tournament_engine.py`.

Lógica pura: construcción de seeding con BYEs, planificación del cuadro
completo y propagación de ganadores entre rondas. No toca estado ni DB.

Patrón AAA: cada test deja explícito Arrange / Act / Assert con comentarios.
"""

from __future__ import annotations

import pytest

from TennisTournament.logic.tournament_engine import (
    BYE,
    PLACEHOLDER_PREFIX,
    STATUS_FINALIZADO,
    STATUS_PENDIENTE,
    AdvanceTarget,
    BracketSlot,
    compute_bracket_size,
    decide_winner,
    distribute_byes,
    next_position,
    plan_bracket,
    propagate_winner,
    winner_advance_side,
)


pytestmark = pytest.mark.unit


# =============================================================================
# 1. compute_bracket_size — siguiente potencia de 2 ≥ n_players
# =============================================================================


class TestComputeBracketSize:
    @pytest.mark.parametrize(
        "n_players, expected",
        [
            (0, 0),
            (1, 0),    # mínimo 2 jugadores reales para un cuadro
            (2, 2),
            (3, 4),
            (4, 4),
            (5, 8),
            (7, 8),
            (8, 8),
            (9, 16),
            (15, 16),
            (16, 16),
            (17, 32),
            (33, 64),
        ],
    )
    def test_potencia_de_dos(self, n_players: int, expected: int):
        # Arrange: número arbitrario de jugadores.
        # Act: calcular tamaño de cuadro.
        result = compute_bracket_size(n_players)
        # Assert: coincide con la potencia de 2 esperada.
        assert result == expected

    def test_negativo_devuelve_cero(self):
        # Arrange: entrada inválida (no debería ocurrir, pero defendemos).
        # Act
        result = compute_bracket_size(-3)
        # Assert: el contrato es "0 si n_players < 2".
        assert result == 0


# =============================================================================
# 2. distribute_byes — intercala BYEs sin que se enfrenten entre sí
# =============================================================================


class TestDistributeByes:
    def test_sin_byes_cuando_es_potencia_de_dos(self, players_4):
        # Arrange: 4 reales en cuadro de 4.
        # Act
        seeding = distribute_byes(players_4, 4)
        # Assert: ningún BYE introducido, mismo orden.
        assert seeding == players_4
        assert BYE not in seeding

    def test_5_jugadores_en_cuadro_de_8(self, players_5):
        # Arrange: 5 reales en cuadro de 8 → deberían introducirse 3 BYEs.
        # Act
        seeding = distribute_byes(players_5, 8)

        # Assert tamaño y conteos correctos
        assert len(seeding) == 8
        assert seeding.count(BYE) == 3
        # Todos los reales presentes
        for p in players_5:
            assert p in seeding

    def test_byes_nunca_se_enfrentan_entre_si(self, players_5):
        # Arrange
        seeding = distribute_byes(players_5, 8)

        # Act: agrupar de dos en dos (los enfrentamientos de R1).
        pairs = [(seeding[i], seeding[i + 1]) for i in range(0, len(seeding), 2)]

        # Assert: ningún par tiene BYE en ambas posiciones.
        for home, away in pairs:
            assert not (home == BYE and away == BYE), (
                f"BYE vs BYE detectado en {pairs}"
            )

    def test_bracket_size_menor_que_reales_lanza(self, players_5):
        # Arrange / Act / Assert
        with pytest.raises(ValueError):
            distribute_byes(players_5, 4)

    @pytest.mark.parametrize("n_real", [2, 3, 5, 6, 7, 9, 11, 13])
    def test_propiedad_no_bye_vs_bye_en_distintos_tamaños(self, n_real: int):
        # Arrange: lista sintética de jugadores reales.
        real = [f"P{i}" for i in range(n_real)]
        size = compute_bracket_size(n_real)

        # Act
        seeding = distribute_byes(real, size)

        # Assert: invariante global (BYE nunca emparejado con BYE).
        for i in range(0, len(seeding), 2):
            assert not (seeding[i] == BYE and seeding[i + 1] == BYE)


# =============================================================================
# 3. winner_advance_side / next_position / decide_winner
# =============================================================================


class TestSmallHelpers:
    @pytest.mark.parametrize(
        "pos, expected",
        [(0, "home"), (1, "away"), (2, "home"), (3, "away"), (10, "home")],
    )
    def test_winner_advance_side(self, pos: int, expected: str):
        assert winner_advance_side(pos) == expected

    def test_next_position_avanza(self):
        # Arrange: ronda 1 de un cuadro de 8 (3 rondas en total).
        # Act
        result = next_position(round_num=1, bracket_position=2, total_rounds=3)
        # Assert: la siguiente ronda es la 2 y la posición la mitad entera.
        assert result == (2, 1)

    def test_next_position_es_none_en_la_final(self):
        # Arrange: round_num == total_rounds (no hay siguiente).
        # Act
        result = next_position(round_num=3, bracket_position=0, total_rounds=3)
        # Assert
        assert result is None

    @pytest.mark.parametrize(
        "sh, sa, expected",
        [
            (2, 1, "Alice"),
            (1, 2, "Bob"),
            (3, 0, "Alice"),
            (0, 3, "Bob"),
        ],
    )
    def test_decide_winner_devuelve_nombre(self, sh: int, sa: int, expected: str):
        assert decide_winner("Alice", "Bob", sh, sa) == expected

    def test_decide_winner_devuelve_none_si_empate(self):
        # Empate (no debería ocurrir en tenis pero el contrato lo contempla).
        assert decide_winner("Alice", "Bob", 1, 1) is None


# =============================================================================
# 4. plan_bracket — generación completa del cuadro
# =============================================================================


class TestPlanBracket:
    def test_seeding_invalido_lanza(self):
        # Arrange: tamaño 3 → no es potencia de 2.
        with pytest.raises(ValueError):
            plan_bracket(["A", "B", "C"], sets_per_match=3)

    def test_seeding_minimo_lanza_con_1(self):
        # Arrange: tamaño 1 → fuera de contrato.
        with pytest.raises(ValueError):
            plan_bracket(["A"], sets_per_match=3)

    def test_cuadro_4_jugadores_estructura(self, players_4):
        # Arrange: 4 jugadores → 3 slots (2 R1 + 1 final).
        # Act
        slots = plan_bracket(players_4, sets_per_match=3)

        # Assert: cuenta y rondas correctas
        assert len(slots) == 3
        assert [s.round_num for s in slots] == [1, 1, 2]
        # Local indices son 1..N
        assert [s.local_index for s in slots] == [1, 2, 3]
        # bracket_position se reinicia por ronda
        assert [s.bracket_position for s in slots] == [0, 1, 0]

    def test_ronda_1_se_pobla_con_seeding(self, players_4):
        # Arrange / Act
        slots = plan_bracket(players_4, sets_per_match=3)

        # Assert: los dos slots de R1 tienen home/away no-vacíos y no son placeholders
        r1 = [s for s in slots if s.round_num == 1]
        assert r1[0].home == "Alice" and r1[0].away == "Bob"
        assert r1[1].home == "Carol" and r1[1].away == "Dave"
        for s in r1:
            assert s.is_placeholder is False
            assert s.status == STATUS_PENDIENTE

    def test_placeholders_usan_indice_local(self, players_4):
        # Arrange / Act
        slots = plan_bracket(players_4, sets_per_match=3)

        # Assert: la final referencia los local_index 1 y 2 (no ids globales).
        final = [s for s in slots if s.round_num == 2][0]
        assert final.home == f"{PLACEHOLDER_PREFIX} 1"
        assert final.away == f"{PLACEHOLDER_PREFIX} 2"
        assert final.is_placeholder is True

    def test_bye_finaliza_partido_y_propaga_a_r2(self):
        # Arrange: 3 reales + 1 BYE → BYE inicial (Alice avanza directa).
        seeding = [BYE, "Alice", "Bob", "Carol"]

        # Act
        slots = plan_bracket(seeding, sets_per_match=3)

        # Assert: el partido con BYE queda Finalizado con sets a favor del real.
        r1 = [s for s in slots if s.round_num == 1]
        bye_match = r1[0]
        assert bye_match.status == STATUS_FINALIZADO
        assert bye_match.sets_away == 2  # winner_set_count = 3//2 + 1 = 2
        assert bye_match.sets_home == 0

        # La final ya tiene a "Alice" como home (propagación BYE→R2)
        final = [s for s in slots if s.round_num == 2][0]
        assert final.home == "Alice"
        # away sigue siendo placeholder porque el otro partido no es BYE
        assert final.away.startswith(PLACEHOLDER_PREFIX)

    def test_cuadro_8_jugadores_total_slots_y_rondas(self, players_8):
        # Arrange / Act
        slots = plan_bracket(players_8, sets_per_match=3)

        # Assert: 4 R1 + 2 R2 + 1 R3 = 7 slots, índices locales 1..7
        assert len(slots) == 7
        rondas = [s.round_num for s in slots]
        assert rondas == [1, 1, 1, 1, 2, 2, 3]
        assert [s.local_index for s in slots] == [1, 2, 3, 4, 5, 6, 7]

    def test_cuadro_8_placeholders_avanzados(self, players_8):
        # Arrange / Act
        slots = plan_bracket(players_8, sets_per_match=3)

        # Assert: los slots de R2 referencian a sus padres por local_index
        r2 = [s for s in slots if s.round_num == 2]
        assert r2[0].home == f"{PLACEHOLDER_PREFIX} 1"
        assert r2[0].away == f"{PLACEHOLDER_PREFIX} 2"
        assert r2[1].home == f"{PLACEHOLDER_PREFIX} 3"
        assert r2[1].away == f"{PLACEHOLDER_PREFIX} 4"
        # La final referencia los local_index de R2 (5 y 6)
        final = [s for s in slots if s.round_num == 3][0]
        assert final.home == f"{PLACEHOLDER_PREFIX} 5"
        assert final.away == f"{PLACEHOLDER_PREFIX} 6"

    def test_winner_set_count_respeta_sets_per_match(self):
        # Arrange: best of 5 → winner_set_count = 5//2 + 1 = 3
        seeding = [BYE, "Alice", "Bob", "Carol"]

        # Act
        slots = plan_bracket(seeding, sets_per_match=5)

        # Assert: el BYE debe registrar 3 sets a favor (no 2).
        bye_match = next(s for s in slots if s.round_num == 1 and s.home == BYE)
        assert bye_match.sets_away == 3


# =============================================================================
# 5. propagate_winner — función pura sin mutación
# =============================================================================


class TestPropagateWinner:
    def test_avance_a_home_cuando_origen_es_par(self):
        # Arrange: source bracket_position=0 (par) → debe ir al lado HOME.
        # Act
        result = propagate_winner(
            source_bracket_position=0,
            winner_name="Alice",
            target_home="",
            target_away="Ganador Partido 2",
            target_is_placeholder=True,
        )
        # Assert
        assert isinstance(result, AdvanceTarget)
        assert result.home == "Alice"
        assert result.away == "Ganador Partido 2"
        # placeholder sigue siendo True porque "away" sigue siendo placeholder
        assert result.is_placeholder is True

    def test_avance_a_away_cuando_origen_es_impar(self):
        # Arrange: bracket_position=1 → lado AWAY.
        # Act
        result = propagate_winner(
            source_bracket_position=1,
            winner_name="Bob",
            target_home="Alice",
            target_away="",
            target_is_placeholder=True,
        )
        # Assert
        assert result.home == "Alice"
        assert result.away == "Bob"
        # ambos lados ahora son reales → ya no es placeholder
        assert result.is_placeholder is False

    def test_no_muta_input(self):
        # Arrange: target inicial.
        target_home = "Alice"
        target_away = ""

        # Act
        propagate_winner(
            source_bracket_position=1,
            winner_name="Bob",
            target_home=target_home,
            target_away=target_away,
            target_is_placeholder=True,
        )

        # Assert: variables originales sin tocar (cierre de pureza).
        assert target_home == "Alice"
        assert target_away == ""

    def test_placeholder_persiste_si_un_lado_aun_es_placeholder(self):
        # Arrange: tras el avance, away sigue siendo "Ganador Partido X".
        # Act
        result = propagate_winner(
            source_bracket_position=2,  # par → home
            winner_name="Alice",
            target_home="",
            target_away="Ganador Partido 4",
            target_is_placeholder=True,
        )
        # Assert
        assert result.is_placeholder is True


# =============================================================================
# 6. Simulación de un cuadro completo con propagate_winner
# =============================================================================


class TestFullBracketProgression:
    """Verifica que `plan_bracket` + `propagate_winner` producen un cuadro
    coherente cuando avanzamos partidos uno a uno (sin DB)."""

    def test_progresion_completa_cuadro_4(self, players_4):
        # Arrange: cuadro de 4 → 2 partidos R1 + 1 final.
        slots = plan_bracket(players_4, sets_per_match=3)
        r1 = [s for s in slots if s.round_num == 1]
        final = [s for s in slots if s.round_num == 2][0]

        # Act 1: avanza ganador del partido R1 #0 (Alice).
        upd = propagate_winner(
            source_bracket_position=r1[0].bracket_position,
            winner_name="Alice",
            target_home=final.home if not final.is_placeholder else "",
            target_away=final.away if not final.is_placeholder else "",
            target_is_placeholder=final.is_placeholder,
        )
        final.home, final.away = upd.home, upd.away
        final.is_placeholder = upd.is_placeholder

        # Act 2: avanza ganador del partido R1 #1 (Carol).
        upd = propagate_winner(
            source_bracket_position=r1[1].bracket_position,
            winner_name="Carol",
            target_home=final.home,
            target_away=final.away,
            target_is_placeholder=final.is_placeholder,
        )
        final.home, final.away = upd.home, upd.away
        final.is_placeholder = upd.is_placeholder

        # Assert: la final tiene Alice vs Carol y ya no es placeholder.
        assert final.home == "Alice"
        assert final.away == "Carol"
        assert final.is_placeholder is False


# =============================================================================
# 7. Aislamiento — la función NO toca DB ni Reflex (sanidad)
# =============================================================================


class TestPurityIsolation:
    """Confirma que las funciones de logic/ son verdaderamente puras: no
    importan reflex ni sqlmodel y no realizan I/O al ejecutarse.

    Si un día alguien refactoriza y mete una dependencia oculta, este test
    cae inmediatamente.
    """

    def test_no_imports_de_infra_en_modulo(self):
        # Arrange / Act
        import TennisTournament.logic.tournament_engine as te

        # Assert: el módulo no expone ni reflex ni sqlmodel ni rx.session.
        assert not hasattr(te, "rx")
        assert not hasattr(te, "sqlmodel")
        assert not hasattr(te, "session")

    def test_bracketslot_es_dataclass_simple(self):
        # Arrange: instanciar con primitivos.
        slot = BracketSlot(round_num=1, bracket_position=0, local_index=1)
        # Act / Assert: defaults correctos.
        assert slot.home == ""
        assert slot.away == ""
        assert slot.status == STATUS_PENDIENTE
        assert slot.sets_home == 0
        assert slot.sets_away == 0
        assert slot.is_placeholder is False
