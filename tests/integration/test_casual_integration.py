"""Tests de integración para `CasualMatchState`.

Valida que el state del formulario "Partido Amistoso" procesa correctamente
los inputs, los steppers de formato y la acción de "Comenzar Partido":
  - asigna los nombres de los jugadores;
  - mantiene `sets_per_match` en valores impares (1, 3, 5, 7, 9);
  - acota `games_per_set` entre 1 y 12;
  - rechaza envíos inválidos (nombres vacíos o duplicados) con `rx.toast`;
  - emite un `rx.redirect` hacia `/scoreboard?casual=1&…` con la config exacta.

`rx.State` bloquea la instanciación directa en runtime para evitar uso
indebido; Reflex deja un escape hatch (`_reflex_internal_init=True`) que es
precisamente el camino soportado en tests. No hay DB ni red.
"""

from __future__ import annotations

import pytest

from TennisTournament.states.casual_match_state import CasualMatchState


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state() -> CasualMatchState:
    """Crea una instancia limpia del state.

    Reflex prohíbe `CasualMatchState()` en tiempo de ejecución normal; el flag
    `_reflex_internal_init=True` es el contrato que el propio framework usa
    para inicializar substates y es el camino válido en tests.
    """
    return CasualMatchState(_reflex_internal_init=True)


def _extract_redirect_url(event_spec) -> str | None:
    """Devuelve la URL de un `EventSpec` de `rx.redirect`, o None si no lo es.

    `rx.redirect("/x")` retorna un EventSpec cuyos `args` son tuplas
    `(Var(name), LiteralVar(value))`. El argumento `path` lleva la URL como
    `LiteralStringVar` con el atributo `_var_value` = string crudo.
    """
    args = getattr(event_spec, "args", None)
    if not args:
        return None
    for name_var, value_var in args:
        if getattr(name_var, "_js_expr", "") == "path":
            return getattr(value_var, "_var_value", None)
    return None


def _is_toast_error(event_spec) -> bool:
    """`rx.toast.error(...)` se compila como un `_call_function` cuya
    expresión JS invoca `refs['__toast']?.['error'](...)`. No es un redirect.
    Comprobamos la firma en los args del EventSpec.
    """
    args = getattr(event_spec, "args", None)
    if not args:
        return False
    for _name_var, value_var in args:
        js = getattr(value_var, "_js_expr", "")
        if "__toast" in js and '"error"' in js:
            return True
    return False


# ---------------------------------------------------------------------------
# 1. Defaults y reset
# ---------------------------------------------------------------------------


class TestDefaultsAndReset:
    def test_defaults_iniciales(self):
        # Arrange / Act
        s = _make_state()
        # Assert: valores por defecto razonables para "al mejor de 3 a 6 juegos".
        assert s.player_j1 == ""
        assert s.player_j2 == ""
        assert s.sets_per_match == 3
        assert s.games_per_set == 6

    def test_setup_page_resetea_a_defaults(self):
        # Arrange: state con datos previos (simula volver al formulario).
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j2("Bob")
        s.increment_sets()  # 3 -> 5
        s.increment_games()  # 6 -> 7
        # Act
        s.setup_page()
        # Assert
        assert s.player_j1 == ""
        assert s.player_j2 == ""
        assert s.sets_per_match == 3
        assert s.games_per_set == 6


# ---------------------------------------------------------------------------
# 2. Asignación de nombres
# ---------------------------------------------------------------------------


class TestPlayerNames:
    def test_set_player_j1_asigna_valor(self):
        s = _make_state()
        s.set_player_j1("Alice")
        assert s.player_j1 == "Alice"

    def test_set_player_j2_asigna_valor(self):
        s = _make_state()
        s.set_player_j2("Bob")
        assert s.player_j2 == "Bob"

    def test_nombres_se_pueden_actualizar_varias_veces(self):
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j1("Carlos")
        assert s.player_j1 == "Carlos"

    def test_nombres_independientes(self):
        # Modificar J1 no debe afectar a J2.
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j2("Bob")
        s.set_player_j1("Eve")
        assert s.player_j1 == "Eve"
        assert s.player_j2 == "Bob"


# ---------------------------------------------------------------------------
# 3. Stepper de sets (solo valores impares: 1, 3, 5, 7, 9)
# ---------------------------------------------------------------------------


class TestSetsStepper:
    def test_incrementa_de_3_a_5(self):
        s = _make_state()
        s.increment_sets()
        assert s.sets_per_match == 5

    def test_secuencia_completa_de_incrementos_solo_impares(self):
        s = _make_state()  # arranca en 3
        valores = [s.sets_per_match]
        for _ in range(10):
            s.increment_sets()
            valores.append(s.sets_per_match)
        # Debe quedar capado en 9 y nunca pasar por números pares.
        assert max(valores) == 9
        assert all(v % 2 == 1 for v in valores), valores
        assert valores[-1] == 9  # techo

    def test_decrementa_a_1_minimo(self):
        s = _make_state()
        for _ in range(10):
            s.decrement_sets()
        assert s.sets_per_match == 1

    def test_no_decrementa_por_debajo_de_1(self):
        s = _make_state()
        for _ in range(5):
            s.decrement_sets()
        s.decrement_sets()
        assert s.sets_per_match == 1


# ---------------------------------------------------------------------------
# 4. Stepper de juegos (rango 1..12)
# ---------------------------------------------------------------------------


class TestGamesStepper:
    def test_incrementa_uno_a_uno(self):
        s = _make_state()
        s.increment_games()
        assert s.games_per_set == 7

    def test_capado_en_12(self):
        s = _make_state()
        for _ in range(20):
            s.increment_games()
        assert s.games_per_set == 12

    def test_decrementa_hasta_1(self):
        s = _make_state()
        for _ in range(20):
            s.decrement_games()
        assert s.games_per_set == 1


# ---------------------------------------------------------------------------
# 5. start_match: validación y redirect
# ---------------------------------------------------------------------------


class TestStartMatch:
    def test_redirige_con_url_correcta(self):
        # Arrange: formulario completo y formato no-default.
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j2("Bob")
        s.increment_sets()  # 3 -> 5
        s.decrement_games()  # 6 -> 5
        # Act
        event = s.start_match()
        # Assert: EventSpec de redirect a /scoreboard con params correctos.
        url = _extract_redirect_url(event)
        assert url is not None, f"start_match no emitió redirect: {event!r}"
        assert url.startswith("/scoreboard?casual=1")
        assert "p1=Alice" in url
        assert "p2=Bob" in url
        assert "sets=5" in url
        assert "games=5" in url

    def test_url_codifica_espacios_y_caracteres_especiales(self):
        # Arrange: nombres con espacios y acentos (URL-encoding obligatorio).
        s = _make_state()
        s.set_player_j1("Juan Pérez")
        s.set_player_j2("María Ñ")
        # Act
        event = s.start_match()
        # Assert
        url = _extract_redirect_url(event)
        assert url is not None
        # Espacios → %20, acentos en UTF-8 → %XX%XX. No queremos espacios crudos.
        assert " " not in url
        assert "p1=Juan%20P%C3%A9rez" in url
        assert "p2=Mar%C3%ADa%20%C3%91" in url

    def test_recorta_espacios_en_los_nombres(self):
        s = _make_state()
        s.set_player_j1("  Alice  ")
        s.set_player_j2("  Bob  ")
        event = s.start_match()
        url = _extract_redirect_url(event)
        assert url is not None
        # Tras strip los nombres viajan limpios: "Alice" y "Bob".
        assert "p1=Alice" in url
        assert "p2=Bob" in url

    def test_default_emite_url_con_3_sets_y_6_juegos(self):
        # Arrange: sólo nombres, sin tocar steppers.
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j2("Bob")
        # Act
        event = s.start_match()
        url = _extract_redirect_url(event)
        # Assert: la URL refleja la configuración por defecto del formulario.
        assert url is not None
        assert "sets=3" in url
        assert "games=6" in url

    @pytest.mark.parametrize(
        "p1, p2",
        [
            ("", "Bob"),
            ("Alice", ""),
            ("", ""),
            ("   ", "Bob"),
            ("Alice", "   "),
        ],
    )
    def test_rechaza_nombres_vacios(self, p1, p2):
        # Arrange
        s = _make_state()
        s.set_player_j1(p1)
        s.set_player_j2(p2)
        # Act
        event = s.start_match()
        # Assert: no se emite redirect; se emite toast de error.
        assert _extract_redirect_url(event) is None
        assert _is_toast_error(event)

    def test_rechaza_nombres_duplicados_case_insensitive(self):
        # Arrange
        s = _make_state()
        s.set_player_j1("Alice")
        s.set_player_j2("alice")  # mismo nombre con distinto case
        # Act
        event = s.start_match()
        # Assert
        assert _extract_redirect_url(event) is None
        assert _is_toast_error(event)


# ---------------------------------------------------------------------------
# 6. Flujo completo: rellenar formulario → comenzar → URL final
# ---------------------------------------------------------------------------


class TestFullFormFlow:
    def test_flujo_completo_form_a_redirect(self):
        """Simula el recorrido real del usuario en el formulario."""
        # Arrange: state limpio (como al entrar a /casual-match).
        s = _make_state()
        s.setup_page()

        # Act: el usuario rellena nombres y ajusta el formato.
        s.set_player_j1("Rafa")
        s.set_player_j2("Roger")
        s.increment_sets()  # 3 -> 5 (al mejor de 5 sets)
        s.decrement_games()
        s.decrement_games()  # 6 -> 4 (sets cortos a 4 juegos)

        # Estado intermedio coherente con lo que mostraría la UI.
        assert s.player_j1 == "Rafa"
        assert s.player_j2 == "Roger"
        assert s.sets_per_match == 5
        assert s.games_per_set == 4

        # Act final: pulsar "Comenzar Partido".
        event = s.start_match()

        # Assert: redirect al scoreboard con TODA la config en la URL.
        url = _extract_redirect_url(event)
        assert url is not None
        assert url == (
            "/scoreboard?casual=1&p1=Rafa&p2=Roger&sets=5&games=4"
        )
