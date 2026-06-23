"""Página "Partido Amistoso" — formulario rápido para jugar sin competición."""

from __future__ import annotations

import reflex as rx

from ..components.bottom_nav import bottom_nav
from ..components.material_icon import material_icon
from ..states.casual_match_state import CasualMatchState


# ============================ Top bar ============================

def _top() -> rx.Component:
    return rx.el.header(
        rx.el.button(
            material_icon("arrow_back", class_name="text-2xl"),
            on_click=rx.redirect("/"),
            aria_label="Volver",
            class_name=(
                "text-primary hover:bg-surface-container transition-colors "
                "active:scale-95 transition-transform duration-150 "
                "p-2 rounded-full flex items-center justify-center"
            ),
        ),
        rx.el.h1(
            "Partido Amistoso",
            class_name="text-lg font-black text-on-surface",
        ),
        rx.box(class_name="w-10"),
        class_name=(
            "bg-surface-container-lowest font-semibold tracking-tight top-0 sticky z-50 "
            "border-b border-surface-container shadow-sm "
            "flex items-center justify-between px-4 h-14 w-full"
        ),
    )


# ============================ Cards =============================

def _card(*children, accent: bool = False) -> rx.Component:
    base = (
        "bg-surface-container-lowest rounded-md "
        "shadow-[0_4px_12px_rgba(31,41,55,0.04)] p-md "
        "border border-surface-variant"
    )
    if accent:
        base += " relative overflow-hidden"
    return rx.el.section(*children, class_name=base)


def _player_input(label: str, value, on_change, placeholder: str) -> rx.Component:
    return rx.box(
        rx.el.label(
            label,
            class_name="block text-label-bold text-on-surface-variant mb-xs",
        ),
        rx.box(
            material_icon("person", class_name="text-outline mr-sm"),
            rx.el.input(
                placeholder=placeholder,
                value=value,
                on_change=on_change,
                type="text",
                class_name=(
                    "w-full bg-transparent border-none p-0 focus:ring-0 outline-none "
                    "text-on-surface text-body-md"
                ),
            ),
            class_name=(
                "bg-surface-container-lowest border border-outline-variant "
                "rounded min-h-[48px] px-sm py-xs flex items-center "
                "focus-within:border-primary-container "
                "focus-within:ring-2 focus-within:ring-primary-container/20 "
                "transition-colors"
            ),
        ),
        class_name="space-y-xs",
    )


def _players_card() -> rx.Component:
    return _card(
        rx.box(class_name="absolute left-0 top-0 bottom-0 w-[4px] bg-primary-container"),
        rx.el.h2(
            "Jugadores",
            class_name="text-headline-lg text-on-surface mb-md ml-xs",
        ),
        rx.box(
            _player_input(
                "Jugador 1",
                CasualMatchState.player_j1,
                CasualMatchState.set_player_j1,
                "Nombre del jugador 1",
            ),
            _player_input(
                "Jugador 2",
                CasualMatchState.player_j2,
                CasualMatchState.set_player_j2,
                "Nombre del jugador 2",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-md ml-xs",
        ),
        accent=True,
    )


# ---------- Stepper compartido visualmente con tournament_config ----------

def _stepper(label: str, value, on_dec, on_inc) -> rx.Component:
    minus_btn = rx.el.button(
        material_icon("remove"),
        on_click=on_dec,
        class_name=(
            "w-10 h-10 flex items-center justify-center "
            "bg-surface-container-lowest border border-outline-variant rounded "
            "text-on-surface hover:bg-primary-container transition-colors"
        ),
    )
    plus_btn = rx.el.button(
        material_icon("add"),
        on_click=on_inc,
        class_name=(
            "w-10 h-10 flex items-center justify-center "
            "bg-primary-container text-on-primary-fixed rounded "
            "hover:opacity-90 transition-colors"
        ),
    )
    return rx.box(
        rx.el.label(
            label,
            class_name="block text-label-bold text-on-surface-variant mb-sm text-center",
        ),
        rx.box(
            rx.box(
                minus_btn,
                rx.el.span(value, class_name="w-12 text-center text-headline-lg"),
                plus_btn,
                class_name=(
                    "flex items-center space-x-4 bg-surface-container-low "
                    "rounded p-1 w-fit"
                ),
            ),
            class_name="flex space-x-sm justify-center",
        ),
    )


def _format_card() -> rx.Component:
    return _card(
        rx.el.h2(
            "Formato de Partido",
            class_name="text-headline-lg mb-md text-on-surface",
        ),
        rx.box(
            _stepper(
                "Sets por partido",
                CasualMatchState.sets_per_match,
                CasualMatchState.decrement_sets,
                CasualMatchState.increment_sets,
            ),
            _stepper(
                "Juegos por set",
                CasualMatchState.games_per_set,
                CasualMatchState.decrement_games,
                CasualMatchState.increment_games,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-md",
        ),
    )


# ============================ Action ============================

def _action_area() -> rx.Component:
    return rx.box(
        rx.el.button(
            material_icon("sports_tennis", class_name="text-2xl"),
            rx.el.span("Comenzar Partido", class_name="ml-xs"),
            on_click=CasualMatchState.start_match,
            class_name=(
                "w-full md:w-80 bg-primary-container text-on-primary-fixed "
                "rounded-md px-xl py-sm min-h-[48px] text-[20px] font-bold "
                "flex items-center justify-center "
                "hover:opacity-90 hover:shadow-inner transition-all"
            ),
        ),
        class_name="flex justify-center pt-sm",
    )


# ============================= Page =============================

def casual_match() -> rx.Component:
    return rx.box(
        _top(),
        rx.el.main(
            _players_card(),
            _format_card(),
            _action_area(),
            class_name=(
                "flex-grow p-container-padding md:p-lg max-w-4xl mx-auto w-full "
                "pb-24 md:pb-lg space-y-lg"
            ),
        ),
        bottom_nav(),
        class_name=(
            "bg-background text-on-background min-h-screen flex flex-col font-sans"
        ),
    )
