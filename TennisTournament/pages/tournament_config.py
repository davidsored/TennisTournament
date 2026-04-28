"""Página de configuración de torneo / liga.

Réplica del blueprint Stitch: top bar con back, tres cards (detalles, formato,
jugadores) y botón "Guardar Configuración" cableado a `ConfigState.save_config`.
"""

from __future__ import annotations

import reflex as rx

from ..components.bottom_nav import bottom_nav
from ..components.material_icon import material_icon
from ..states.config_state import ConfigState


# ============================ Top bar ============================

def _config_top_bar() -> rx.Component:
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
            "Configuración de Torneo",
            class_name="text-lg font-black text-on-surface",
        ),
        rx.el.button(
            material_icon("more_vert", class_name="text-2xl"),
            aria_label="Más opciones",
            class_name=(
                "text-primary hover:bg-surface-container transition-colors "
                "active:scale-95 transition-transform duration-150 "
                "p-2 rounded-full flex items-center justify-center"
            ),
        ),
        class_name=(
            "bg-surface-container-lowest font-semibold tracking-tight top-0 sticky z-50 "
            "border-b border-surface-container shadow-sm "
            "flex items-center justify-between px-4 h-14 w-full"
        ),
    )


# ============================ Cards =============================

def _card(*children, accent: bool = False) -> rx.Component:
    """Tarjeta blanca con sombra suave y borde sutil (sistema Advantage)."""
    base = (
        "bg-surface-container-lowest rounded-md "
        "shadow-[0_4px_12px_rgba(31,41,55,0.04)] p-md "
        "border border-surface-variant"
    )
    if accent:
        base += " relative overflow-hidden"
    return rx.el.section(*children, class_name=base)


def _details_card() -> rx.Component:
    return _card(
        rx.el.h2(
            "Detalles del Torneo",
            class_name="text-headline-lg mb-sm text-on-surface",
        ),
        rx.box(
            rx.el.label(
                "Nombre del Torneo",
                html_for="tournament-name",
                class_name="block text-label-bold text-on-surface-variant mb-xs",
            ),
            rx.el.input(
                id="tournament-name",
                placeholder="Ej. Torneo de Verano 2024",
                value=ConfigState.tournament_name,
                on_change=ConfigState.set_tournament_name,
                type="text",
                class_name=(
                    "w-full bg-surface-container-lowest border border-outline-variant "
                    "rounded min-h-[48px] px-sm py-xs "
                    "focus:outline-none focus:border-primary-container "
                    "focus:ring-2 focus:ring-primary-container/20 transition-colors "
                    "text-on-surface text-body-md placeholder:text-outline"
                ),
            ),
            class_name="space-y-sm",
        ),
    )


# ----------- Stepper numérico (-, valor, +) -----------

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
                ConfigState.sets_per_match,
                ConfigState.decrement_sets,
                ConfigState.increment_sets,
            ),
            _stepper(
                "Juegos por set",
                ConfigState.games_per_set,
                ConfigState.decrement_games,
                ConfigState.increment_games,
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-md",
        ),
    )


# ------------- Lista dinámica de jugadores -------------

def _player_row(player, idx) -> rx.Component:
    input_box = rx.box(
        material_icon("person", class_name="text-outline mr-sm"),
        rx.el.input(
            placeholder="Nombre del jugador",
            value=player,
            on_change=lambda v: ConfigState.update_player(idx, v),
            type="text",
            class_name=(
                "w-full bg-transparent border-none p-0 focus:ring-0 outline-none "
                "text-on-surface text-body-md"
            ),
        ),
        class_name=(
            "flex-grow bg-surface-container-lowest border border-outline-variant "
            "rounded min-h-[48px] px-sm py-xs flex items-center "
            "focus-within:border-primary-container "
            "focus-within:ring-2 focus-within:ring-primary-container/20 transition-colors"
        ),
    )
    delete_btn = rx.el.button(
        material_icon("delete"),
        on_click=lambda: ConfigState.remove_player(idx),
        aria_label="Eliminar jugador",
        class_name=(
            "min-h-[48px] w-[48px] flex items-center justify-center "
            "rounded border border-outline-variant text-error "
            "hover:bg-error-container hover:border-error-container transition-colors"
        ),
    )
    return rx.box(
        input_box,
        delete_btn,
        class_name="flex items-center space-x-sm group",
    )


def _players_card() -> rx.Component:
    return _card(
        # Acento lateral izquierdo
        rx.box(class_name="absolute left-0 top-0 bottom-0 w-[4px] bg-primary-container"),
        # Header con título + pill de inscritos
        rx.box(
            rx.el.h2(
                "Lista de Jugadores",
                class_name="text-headline-lg text-on-surface",
            ),
            rx.el.span(
                ConfigState.registered_label,
                class_name=(
                    "bg-surface-container-highest text-on-surface-variant "
                    "px-sm py-1 rounded-full text-label-bold"
                ),
            ),
            class_name="flex items-center justify-between mb-md ml-xs",
        ),
        # Filas
        rx.box(
            rx.foreach(ConfigState.players, _player_row),
            class_name="space-y-sm ml-xs",
        ),
        # Añadir jugador
        rx.el.button(
            material_icon("add"),
            rx.el.span("Añadir Jugador"),
            on_click=ConfigState.add_player,
            class_name=(
                "mt-md ml-xs flex items-center justify-center space-x-2 "
                "bg-transparent border-2 border-primary-container text-on-surface "
                "rounded-md px-md py-sm min-h-[48px] text-label-bold "
                "hover:bg-primary-container hover:text-on-primary-fixed transition-colors"
            ),
        ),
        accent=True,
    )


# ============================ Action ============================

def _action_area() -> rx.Component:
    return rx.box(
        rx.el.button(
            "Guardar Configuración",
            on_click=ConfigState.save_config,
            class_name=(
                "w-full md:w-80 bg-primary-container text-on-primary-fixed "
                "rounded-md px-xl py-sm min-h-[48px] text-[20px] font-bold "
                "hover:opacity-90 hover:shadow-inner transition-all"
            ),
        ),
        class_name="flex justify-center pt-sm",
    )


# ============================= Page =============================

def tournament_config() -> rx.Component:
    return rx.box(
        _config_top_bar(),
        rx.el.main(
            _details_card(),
            _format_card(),
            _players_card(),
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
