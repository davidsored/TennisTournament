"""Diálogo "Editar participantes" de los dashboards de liga y torneo.

Lista los participantes de la competición activa con edición inline por
fila: lápiz → input + Guardar/Cancelar, con validación de duplicados en
`logic.players.plan_rename` (vía `LeagueState.rename_player`). Mismo estilo
visual que el diálogo de administrador de la home.
"""

from __future__ import annotations

import reflex as rx

from ..states.player_edit_state import PlayerEditState
from .dialog_style import DIALOG_CONTENT_STYLE
from .material_icon import material_icon


def edit_players_button(comp_id: rx.Var[int] | int, comp_type: str) -> rx.Component:
    """Botón-lápiz redondo que abre el diálogo para la competición dada."""
    return rx.el.button(
        material_icon("edit", class_name="text-xl"),
        on_click=lambda: PlayerEditState.open_dialog(comp_id, comp_type),
        aria_label="Editar participantes",
        class_name=(
            "w-10 h-10 flex items-center justify-center rounded-full "
            "text-on-surface-variant hover:bg-surface-container "
            "active:bg-surface-container-high transition-colors"
        ),
    )


def _row_display(name: rx.Var[str]) -> rx.Component:
    """Fila normal: nombre + lápiz para entrar en edición."""
    return rx.box(
        rx.el.span(
            name,
            class_name="text-label-bold text-on-surface truncate",
        ),
        rx.el.button(
            material_icon("edit", class_name="text-lg"),
            on_click=lambda: PlayerEditState.start_edit(name),
            aria_label="Editar nombre",
            class_name=(
                "w-9 h-9 flex items-center justify-center rounded-full "
                "text-on-surface-variant hover:bg-surface-container "
                "transition-colors shrink-0"
            ),
        ),
        class_name="flex items-center justify-between gap-sm",
    )


def _row_editing() -> rx.Component:
    """Fila en edición: input + error + Guardar/Cancelar."""
    return rx.box(
        rx.el.input(
            value=PlayerEditState.input_value,
            on_change=PlayerEditState.set_input_value,
            placeholder="Nombre del participante",
            auto_focus=True,
            class_name=(
                "w-full bg-surface-container-lowest border border-outline-variant "
                "rounded min-h-[48px] px-sm py-xs "
                "focus:outline-none focus:border-primary-container "
                "focus:ring-2 focus:ring-primary-container/20 transition-colors "
                "text-on-surface text-body-md placeholder:text-outline"
            ),
        ),
        rx.cond(
            PlayerEditState.error_message != "",
            rx.el.p(
                PlayerEditState.error_message,
                class_name="text-error text-sm mt-xs",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.el.button(
                "Cancelar",
                on_click=PlayerEditState.cancel_edit,
                class_name=(
                    "px-md py-sm rounded text-label-bold "
                    "text-on-surface-variant hover:bg-surface-container "
                    "transition-colors"
                ),
            ),
            rx.el.button(
                "Guardar",
                on_click=PlayerEditState.save_edit,
                class_name=(
                    "px-md py-sm rounded bg-primary-container "
                    "text-on-primary-fixed text-label-bold "
                    "hover:opacity-90 transition-opacity"
                ),
            ),
            class_name="flex justify-end gap-sm mt-sm",
        ),
        class_name="flex flex-col w-full",
    )


def _player_row(name: rx.Var[str]) -> rx.Component:
    return rx.box(
        rx.cond(
            PlayerEditState.editing_name == name,
            _row_editing(),
            _row_display(name),
        ),
        class_name=(
            "px-sm py-xs rounded-md bg-surface-container-low "
            "border border-outline-variant/40"
        ),
    )


def edit_players_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                "Editar participantes",
                class_name="text-headline-lg text-on-surface mb-xs",
            ),
            rx.dialog.description(
                "El nombre se actualiza en la clasificación y en todos los partidos.",
                class_name="text-body-md text-on-surface-variant mb-md",
            ),
            rx.box(
                rx.foreach(PlayerEditState.players, _player_row),
                class_name="flex flex-col gap-xs max-h-[60vh] overflow-y-auto",
            ),
            rx.box(
                rx.dialog.close(
                    rx.el.button(
                        "Cerrar",
                        class_name=(
                            "px-md py-sm rounded text-label-bold "
                            "text-on-surface-variant hover:bg-surface-container "
                            "transition-colors"
                        ),
                    ),
                ),
                class_name="flex justify-end mt-md",
            ),
            style=DIALOG_CONTENT_STYLE,
        ),
        open=PlayerEditState.dialog_open,
        on_open_change=PlayerEditState.set_dialog_open,
    )
