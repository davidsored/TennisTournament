"""Modal "¿Quién comienza sacando?" del marcador.

Aparece antes del primer punto de cualquier partido (amistoso, liga o torneo)
mientras `ScoreboardState.server_chosen` sea False. No es descartable: la
única salida es elegir a uno de los dos jugadores. Mismo estilo visual que
el diálogo de administrador de la home.
"""

from __future__ import annotations

import reflex as rx

from ..states.scoreboard_state import ScoreboardState
from .dialog_style import DIALOG_CONTENT_STYLE
from .material_icon import material_icon


def _server_option(player_name: rx.Var[str], player_id: int) -> rx.Component:
    """Botón grande con el nombre del jugador candidato a sacar primero."""
    return rx.el.button(
        material_icon("sports_tennis", class_name="text-2xl"),
        rx.el.span(player_name, class_name="text-label-bold truncate"),
        on_click=lambda: ScoreboardState.choose_server(player_id),
        class_name=(
            "w-full bg-primary-container text-on-primary-fixed rounded-xl "
            "px-md py-sm flex items-center justify-center gap-xs min-h-[56px] "
            "hover:opacity-90 active:scale-[0.98] transition-all"
        ),
    )


def server_selection_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                "¿Quién comienza sacando?",
                class_name="text-headline-lg text-on-surface mb-xs",
            ),
            rx.dialog.description(
                "Selecciona el jugador que hará el primer saque.",
                class_name="text-body-md text-on-surface-variant mb-md",
            ),
            rx.box(
                _server_option(ScoreboardState.player_j1, 1),
                _server_option(ScoreboardState.player_j2, 2),
                class_name="flex flex-col gap-sm w-full",
            ),
            # Sin on_open_change ni dialog.close: el modal sólo se cierra
            # eligiendo sacador (server_chosen=True → show_server_modal=False).
            style=DIALOG_CONTENT_STYLE,
        ),
        open=ScoreboardState.show_server_modal,
    )
