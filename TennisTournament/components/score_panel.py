"""Panel de marcador compacto reutilizable.

Variante secundaria del marcador (la página `/scoreboard` integra su propia
tabla extendida). Aquí mantenemos un componente más simple por si se reutiliza
en listados o vistas resumen.
"""

from __future__ import annotations

import reflex as rx

from ..states.scoreboard_state import ScoreboardState


def _chip(value, accent: str = "default") -> rx.Component:
    tones = {
        "default": "bg-graphite text-surface-container-lowest",
        "primary": "bg-graphite text-primary-container",
    }
    return rx.el.div(
        value,
        class_name=(
            f"min-w-[3rem] h-12 px-sm flex items-center justify-center "
            f"rounded-md shadow-inner text-score-display {tones[accent]}"
        ),
    )


def _player_row(name, point_visual, games, sets_, is_primary: bool = False) -> rx.Component:
    accent_bar = (
        "border-l-4 border-primary-container" if is_primary else "border-l-4 border-transparent"
    )
    return rx.el.div(
        rx.el.div(
            name,
            class_name="flex-1 px-md py-sm text-body-lg font-semibold text-graphite truncate",
        ),
        rx.el.div(
            _chip(sets_),
            _chip(games),
            _chip(point_visual, accent="primary"),
            class_name="flex items-center gap-xs pr-md",
        ),
        class_name=(
            f"flex items-center {accent_bar} "
            "border-b border-outline-variant last:border-b-0"
        ),
    )


def _column_header() -> rx.Component:
    cell = "w-12 text-center text-label-bold uppercase tracking-wider text-on-surface-variant"
    return rx.el.div(
        rx.el.div("", class_name="flex-1 px-md py-xs"),
        rx.el.div(
            rx.el.span("SET", class_name=cell),
            rx.el.span("GAME", class_name=cell),
            rx.el.span("PT", class_name=cell),
            class_name="flex items-center gap-xs pr-md",
        ),
        class_name="flex items-center border-b border-outline-variant bg-surface-container-low",
    )


def score_panel() -> rx.Component:
    return rx.el.div(
        _column_header(),
        _player_row(
            ScoreboardState.player_j1,
            ScoreboardState.score_visual_j1,
            ScoreboardState.juegos_j1,
            ScoreboardState.sets_j1,
            is_primary=True,
        ),
        _player_row(
            ScoreboardState.player_j2,
            ScoreboardState.score_visual_j2,
            ScoreboardState.juegos_j2,
            ScoreboardState.sets_j2,
            is_primary=False,
        ),
        class_name=(
            "w-full max-w-2xl mx-auto rounded-xl bg-surface-container-lowest "
            "border border-outline-variant shadow-soft overflow-hidden"
        ),
    )
