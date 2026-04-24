"""Página del marcador en vivo — estilo Advantage."""

from __future__ import annotations

import reflex as rx

from ..components.navbar import navbar
from ..components.score_panel import score_panel
from ..states.scoreboard_state import ScoreboardState


def _primary_button(label: str, on_click) -> rx.Component:
    return rx.el.button(
        label,
        on_click=on_click,
        class_name=(
            "min-h-[48px] px-md rounded-lg bg-primary-container text-graphite "
            "text-label-bold uppercase tracking-wider "
            "hover:shadow-[inset_0_0_0_2px_rgba(31,41,55,0.15)] "
            "transition-shadow"
        ),
    )


def _secondary_button(label: str, on_click) -> rx.Component:
    return rx.el.button(
        label,
        on_click=on_click,
        class_name=(
            "min-h-[48px] px-md rounded-lg border border-graphite text-graphite "
            "text-label-bold uppercase tracking-wider "
            "hover:bg-surface-container transition-colors"
        ),
    )


def scoreboard() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.h1(
                "Marcador en vivo",
                class_name="text-headline-xl text-graphite text-center mb-lg",
            ),
            score_panel(),
            rx.el.div(
                _primary_button("+1 Jugador A", ScoreboardState.point_a),
                _primary_button("+1 Jugador B", ScoreboardState.point_b),
                _secondary_button("Reiniciar", ScoreboardState.reset_match),
                class_name="flex flex-wrap justify-center gap-sm mt-lg",
            ),
            class_name="max-w-6xl mx-auto px-sm py-lg",
        ),
        class_name="min-h-screen bg-surface font-sans",
    )
