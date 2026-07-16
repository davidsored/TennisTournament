"""Tests unitarios de `logic.validation` — reglas de configuración.

Validan la función pura que blinda tanto el formulario (`ConfigState`)
como los mutadores server-side (`LeagueState.setup_league/setup_tournament`).
"""

from __future__ import annotations

import pytest

from TennisTournament.logic.validation import (
    validate_competition_config,
    validate_player_name,
    validate_player_names,
)

pytestmark = pytest.mark.unit


VALID_PLAYERS = ["Alice", "Bob"]


class TestValidateCompetitionConfig:
    def test_config_valida_devuelve_none(self):
        assert (
            validate_competition_config("Liga", VALID_PLAYERS, 3, 6) is None
        )

    def test_nombre_vacio_o_solo_espacios(self):
        assert validate_competition_config("", VALID_PLAYERS, 3, 6) is not None
        assert validate_competition_config("   ", VALID_PLAYERS, 3, 6) is not None

    def test_menos_de_dos_jugadores(self):
        assert validate_competition_config("Liga", ["Alice"], 3, 6) is not None
        assert validate_competition_config("Liga", [], 3, 6) is not None
        # Jugadores en blanco no cuentan.
        assert (
            validate_competition_config("Liga", ["Alice", "  "], 3, 6) is not None
        )

    @pytest.mark.parametrize("sets", [0, 2, 4, 6, 8, 10, 11, -1])
    def test_sets_invalidos(self, sets):
        assert (
            validate_competition_config("Liga", VALID_PLAYERS, sets, 6) is not None
        )

    @pytest.mark.parametrize("sets", [1, 3, 5, 7, 9])
    def test_sets_validos(self, sets):
        assert (
            validate_competition_config("Liga", VALID_PLAYERS, sets, 6) is None
        )

    @pytest.mark.parametrize("games", [0, 13, -1, 100])
    def test_games_fuera_de_rango(self, games):
        assert (
            validate_competition_config("Liga", VALID_PLAYERS, 3, games)
            is not None
        )

    @pytest.mark.parametrize("games", [1, 6, 12])
    def test_games_en_rango(self, games):
        assert (
            validate_competition_config("Liga", VALID_PLAYERS, 3, games) is None
        )

    def test_duplicados_case_insensitive(self):
        assert (
            validate_competition_config("Liga", ["Ana", "ana"], 3, 6) is not None
        )
        assert (
            validate_competition_config("Liga", ["Ana", " ANA "], 3, 6)
            is not None
        )

    def test_tres_jugadores_sin_duplicados_ok(self):
        assert (
            validate_competition_config("Liga", ["Ana", "Bea", "Carla"], 3, 6)
            is None
        )


class TestValidatePlayerNames:
    def test_nombre_bye_reservado(self):
        assert validate_player_names(["Alice", "BYE"]) is not None
        assert validate_player_names(["Alice", "bye"]) is not None

    def test_prefijo_placeholder_prohibido(self):
        assert (
            validate_player_names(["Alice", "Ganador Partido 3"]) is not None
        )

    def test_nombres_normales_ok(self):
        assert validate_player_names(["Alice", "Bob", "Carol"]) is None


class TestValidatePlayerName:
    def test_vacio(self):
        assert validate_player_name("") is not None

    def test_nombre_normal(self):
        assert validate_player_name("Alice") is None

    def test_bye_case_insensitive(self):
        assert validate_player_name("ByE") is not None
