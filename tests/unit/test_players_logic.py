"""Tests unitarios de `logic.players.plan_rename`."""

from __future__ import annotations

import pytest

from TennisTournament.logic.players import plan_rename

pytestmark = pytest.mark.unit


PLAYERS = ["Alice", "Bob", "Carol"]


class TestPlanRenameValido:
    def test_renombra_y_preserva_orden(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "Roberto")
        assert err is None
        assert new_list == ["Alice", "Roberto", "Carol"]

    def test_hace_strip_del_nombre_nuevo(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "  Roberto  ")
        assert err is None
        assert new_list == ["Alice", "Roberto", "Carol"]

    def test_cambio_solo_de_mayusculas_permitido(self):
        """Renombrar 'Bob' → 'BOB' es válido (no es duplicado de otro)."""
        new_list, err = plan_rename(PLAYERS, "Bob", "BOB")
        assert err is None
        assert new_list == ["Alice", "BOB", "Carol"]

    def test_no_muta_la_lista_original(self):
        original = list(PLAYERS)
        plan_rename(PLAYERS, "Bob", "Roberto")
        assert PLAYERS == original


class TestPlanRenameInvalido:
    def test_nombre_vacio(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "   ")
        assert new_list is None
        assert err is not None

    def test_old_name_inexistente(self):
        new_list, err = plan_rename(PLAYERS, "Zoe", "Zoa")
        assert new_list is None
        assert err is not None

    def test_sin_cambios(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "Bob")
        assert new_list is None
        assert err is not None

    def test_duplicado_exacto(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "Alice")
        assert new_list is None
        assert err is not None

    def test_duplicado_case_insensitive(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "alice")
        assert new_list is None
        assert err is not None

    def test_nombre_reservado_bye(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "BYE")
        assert new_list is None
        assert err is not None

    def test_prefijo_placeholder_prohibido(self):
        new_list, err = plan_rename(PLAYERS, "Bob", "Ganador Partido 7")
        assert new_list is None
        assert err is not None
