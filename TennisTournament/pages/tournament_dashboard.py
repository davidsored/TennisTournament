"""Tournament Dashboard — vista del cuadro eliminatorio.

Réplica del blueprint Stitch usando los tokens del sistema Advantage. Los datos
proceden de `TournamentState.bracket_columns` (que a su vez agrupa los
`LeagueMatch` por ronda y bracket_position).
"""

from __future__ import annotations

import reflex as rx

from ..components.bottom_nav import bottom_nav
from ..components.edit_players_dialog import edit_players_button, edit_players_dialog
from ..components.material_icon import material_icon
from ..states.tournament_state import TournamentState


# ============================ TopAppBar ============================

def _top_bar() -> rx.Component:
    return rx.el.header(
        rx.box(
            rx.link(
                rx.box(
                    material_icon(
                        "home",
                        fill=True,
                        class_name="text-2xl text-primary",
                    ),
                    class_name=(
                        "w-10 h-10 flex items-center justify-center "
                        "rounded-full hover:bg-surface-container transition-colors"
                    ),
                ),
                href="/",
            ),
            rx.el.span(
                "CourtManager",
                class_name=(
                    "text-lg font-black text-on-surface uppercase tracking-widest "
                    "text-center flex-1"
                ),
            ),
            rx.box(class_name="w-10"),
            class_name=(
                "flex justify-between items-center px-4 h-16 w-full max-w-7xl mx-auto"
            ),
        ),
        class_name=(
            "bg-surface-container-lowest tracking-tight "
            "shadow-[0_2px_15px_-3px_rgba(31,41,55,0.04)] "
            "sticky top-0 z-40 border-b border-surface-container"
        ),
    )


# ============================ Conectores ============================
# Los conectores se posicionan respecto al WRAPPER del match (flex-1
# flex-col justify-center), no respecto al cell. Así las alturas son
# proporcionales al slot del match — algo crítico para que las líneas
# se encuentren entre rondas (50% del wrapper = mitad de la distancia
# al match adyacente, exactamente la mitad del salto al match siguiente).
# Color: theme('colors.outline-variant') = #c4c9ac.

_OL_COLOR = "#c4c9ac"


def _connector_horizontal_out() -> rx.Component:
    """Línea horizontal saliente: del borde derecho del wrapper hasta el midpoint del gap."""
    return rx.box(
        style={
            "position": "absolute",
            "right": "-2rem",
            "top": "50%",
            "width": "2rem",
            "borderTop": f"2px solid {_OL_COLOR}",
            "zIndex": 0,
        },
    )


def _connector_vertical_top() -> rx.Component:
    """Vertical desde el centro del wrapper hacia abajo (50% de su altura).

    Como el wrapper ocupa el slot vertical del match (flex-1), 50% de su
    altura equivale exactamente a la mitad de la distancia hasta el
    siguiente match → la línea termina en el centro del wrapper de la
    ronda siguiente.
    """
    return rx.box(
        style={
            "position": "absolute",
            "right": "-2rem",
            "top": "50%",
            "height": "50%",
            "borderRight": f"2px solid {_OL_COLOR}",
            "zIndex": 0,
        },
    )


def _connector_vertical_bottom() -> rx.Component:
    """Vertical desde el centro del wrapper hacia arriba (50% de su altura)."""
    return rx.box(
        style={
            "position": "absolute",
            "right": "-2rem",
            "bottom": "50%",
            "height": "50%",
            "borderRight": f"2px solid {_OL_COLOR}",
            "zIndex": 0,
        },
    )


def _connector_incoming() -> rx.Component:
    """Línea horizontal entrante: del midpoint del gap al borde izquierdo del wrapper."""
    return rx.box(
        style={
            "position": "absolute",
            "left": "-2rem",
            "top": "50%",
            "width": "2rem",
            "borderTop": f"2px solid {_OL_COLOR}",
            "zIndex": 0,
        },
    )


# ============================ Match Card ============================

def _player_name(name, is_winner, is_placeholder, with_trophy: bool = False) -> rx.Component:
    """Nombre del jugador con etiqueta opcional y trofeo (solo final/champion)."""
    name_class = rx.cond(
        is_placeholder,
        "text-label-bold text-secondary",
        rx.cond(
            is_winner,
            "text-label-bold text-on-surface",
            "text-label-bold text-secondary",
        ),
    )
    label = rx.cond(
        is_winner,
        rx.el.span(
            "Winner",
            class_name="text-xs text-primary font-bold",
        ),
        rx.fragment(),
    )

    body = rx.box(
        rx.el.span(name, class_name=name_class),
        label,
        class_name="flex flex-col",
    )

    if with_trophy:
        return rx.box(
            material_icon(
                "emoji_events",
                fill=True,
                class_name="text-primary-container",
            ),
            body,
            class_name="flex items-center gap-xs",
        )
    return body


def _player_score(score, is_winner, is_placeholder) -> rx.Component:
    return rx.el.span(
        score,
        class_name=rx.cond(
            is_placeholder,
            "text-score-display text-secondary",
            rx.cond(
                is_winner,
                "text-score-display text-on-surface",
                "text-score-display text-secondary",
            ),
        ),
    )


def _player_cell(
    name,
    score,
    is_winner,
    is_placeholder,
) -> rx.Component:
    """Celda de jugador (parte de un match card no-final).

    Los conectores ya NO se dibujan aquí — se han movido al wrapper del match
    para que las líneas se posicionen en proporción al slot, no al cell.
    """
    base = (
        "bg-surface-container-lowest rounded-xl "
        "shadow-[0_2px_15px_-3px_rgba(31,41,55,0.04)] "
        "p-sm flex justify-between items-center"
    )
    winner = base + " border-l-4 border-primary-container"
    loser = base + " opacity-60"
    placeholder = base + " opacity-60"

    cell_class = rx.cond(
        is_placeholder,
        placeholder,
        rx.cond(is_winner, winner, loser),
    )

    return rx.box(
        _player_name(name, is_winner, is_placeholder),
        _player_score(score, is_winner, is_placeholder),
        class_name=cell_class,
    )


def _play_overlay(match_id, show: bool) -> rx.Component:
    """Pequeño botón Play (solo si pendiente y con ambos jugadores reales)."""
    return rx.cond(
        show,
        rx.link(
            rx.box(
                material_icon(
                    "play_arrow",
                    fill=True,
                    class_name="text-on-primary-container text-xl",
                ),
                class_name=(
                    "absolute -top-2 -right-2 w-7 h-7 rounded-full "
                    "bg-primary-container shadow-md flex items-center justify-center "
                    "hover:scale-110 transition-transform z-20"
                ),
            ),
            href=f"/scoreboard?match_id={match_id}",
        ),
        rx.fragment(),
    )


def _match_card_regular(m) -> rx.Component:
    """Match card para rondas no-finales (dos celdas apiladas)."""
    can_play = m.is_pending & m.has_pair
    return rx.box(
        _player_cell(m.home, m.home_score, m.home_winner, m.home_is_placeholder),
        _player_cell(m.away, m.away_score, m.away_winner, m.away_is_placeholder),
        _play_overlay(m.id, can_play),
        class_name="relative flex flex-col gap-base",
    )


def _final_card(m) -> rx.Component:
    """Final con marco destacado, badge y trofeo para el campeón."""
    home_class = rx.cond(
        m.home_winner,
        "bg-surface rounded-lg p-sm flex justify-between items-center border border-primary-container",
        rx.cond(
            m.home_is_placeholder,
            "bg-surface-container rounded-lg p-sm flex justify-between items-center opacity-80",
            rx.cond(
                m.is_finished,
                "bg-surface-container rounded-lg p-sm flex justify-between items-center opacity-80",
                "bg-surface rounded-lg p-sm flex justify-between items-center",
            ),
        ),
    )
    away_class = rx.cond(
        m.away_winner,
        "bg-surface rounded-lg p-sm flex justify-between items-center border border-primary-container",
        rx.cond(
            m.away_is_placeholder,
            "bg-surface-container rounded-lg p-sm flex justify-between items-center opacity-80",
            rx.cond(
                m.is_finished,
                "bg-surface-container rounded-lg p-sm flex justify-between items-center opacity-80",
                "bg-surface rounded-lg p-sm flex justify-between items-center",
            ),
        ),
    )

    # Champion label en lugar de Winner para la final
    home_label = rx.cond(
        m.home_winner,
        rx.el.span("Champion", class_name="text-xs text-primary font-bold"),
        rx.fragment(),
    )
    away_label = rx.cond(
        m.away_winner,
        rx.el.span("Champion", class_name="text-xs text-primary font-bold"),
        rx.fragment(),
    )

    can_play = m.is_pending & m.has_pair

    return rx.box(
        _connector_incoming(),
        rx.box(
            rx.el.span(
                "Final",
                class_name=(
                    "text-label-bold uppercase tracking-wider text-xs "
                    "bg-primary-container text-on-primary-container "
                    "px-2 py-1 rounded-full"
                ),
            ),
            class_name="text-center mb-xs",
        ),
        # Home (campeón si home_winner)
        rx.box(
            rx.box(
                rx.cond(
                    m.home_winner,
                    material_icon(
                        "emoji_events",
                        fill=True,
                        class_name="text-primary-container",
                    ),
                    rx.fragment(),
                ),
                rx.box(
                    rx.el.span(
                        m.home,
                        class_name=rx.cond(
                            m.home_is_placeholder,
                            "text-label-bold text-secondary",
                            rx.cond(
                                m.home_winner,
                                "text-label-bold text-on-surface",
                                "text-label-bold text-secondary",
                            ),
                        ),
                    ),
                    home_label,
                    class_name="flex flex-col",
                ),
                class_name="flex items-center gap-xs",
            ),
            rx.el.span(
                m.home_score,
                class_name=rx.cond(
                    m.home_winner,
                    "text-score-display text-on-surface",
                    "text-score-display text-secondary",
                ),
            ),
            class_name=home_class,
        ),
        # Away (campeón si away_winner)
        rx.box(
            rx.box(
                rx.cond(
                    m.away_winner,
                    material_icon(
                        "emoji_events",
                        fill=True,
                        class_name="text-primary-container",
                    ),
                    rx.fragment(),
                ),
                rx.box(
                    rx.el.span(
                        m.away,
                        class_name=rx.cond(
                            m.away_is_placeholder,
                            "text-label-bold text-secondary",
                            rx.cond(
                                m.away_winner,
                                "text-label-bold text-on-surface",
                                "text-label-bold text-secondary",
                            ),
                        ),
                    ),
                    away_label,
                    class_name="flex flex-col",
                ),
                class_name=rx.cond(
                    m.away_winner,
                    "flex items-center gap-xs",
                    "flex flex-col pl-7",
                ),
            ),
            rx.el.span(
                m.away_score,
                class_name=rx.cond(
                    m.away_winner,
                    "text-score-display text-on-surface",
                    "text-score-display text-secondary",
                ),
            ),
            class_name=away_class,
        ),
        _play_overlay(m.id, can_play),
        class_name=(
            "relative flex flex-col gap-base "
            "bg-surface-container-lowest rounded-xl "
            "shadow-[0_4px_20px_-4px_rgba(31,41,55,0.08)] "
            "p-sm border-2 border-primary-container"
        ),
    )


def _match_node(m) -> rx.Component:
    return rx.cond(m.is_final, _final_card(m), _match_card_regular(m))


# ============================ Match wrapper ============================
# Cada match se envuelve en un slot `flex-1` que se centra verticalmente.
# Como cada wrapper de la ronda N+1 cubre el espacio de DOS wrappers de la
# ronda N (porque hay la mitad de matches), centrar dentro del wrapper
# alinea automáticamente cada match con el midpoint de sus dos padres.
# Los conectores viven aquí porque sus alturas dependen del slot, no del cell.

def _match_wrapper(m) -> rx.Component:
    return rx.box(
        # Conector entrante (rondas > 1): pequeño stub horizontal a la izquierda.
        rx.cond(m.has_incoming, _connector_incoming(), rx.fragment()),
        # El match centrado dentro del slot.
        _match_node(m),
        # Conectores salientes (rondas no-finales).
        rx.cond(m.has_outgoing, _connector_horizontal_out(), rx.fragment()),
        rx.cond(
            m.has_outgoing,
            rx.cond(
                m.is_top_half,
                _connector_vertical_top(),
                rx.cond(
                    m.is_bottom_half,
                    _connector_vertical_bottom(),
                    rx.fragment(),
                ),
            ),
            rx.fragment(),
        ),
        class_name="flex-1 flex flex-col justify-center w-full relative",
    )


# ============================ Column ============================

def _column(col) -> rx.Component:
    """Columna del bracket: stretch vertical y reparte el alto entre sus matches.

    Sin `justify-around` ni padding artificial. La columna toma toda la
    altura del contenedor (vía `align-items: stretch` del flex-row padre)
    y los wrappers `flex-1` reparten ese alto a partes iguales — exactamente
    el comportamiento que necesita el bracket para alinear rondas.
    """
    return rx.box(
        rx.foreach(col.matches, _match_wrapper),
        class_name="flex flex-col w-64 relative z-10",
    )


# ============================ Empty state ============================

def _empty_state() -> rx.Component:
    return rx.box(
        material_icon(
            "emoji_events",
            class_name="text-6xl text-on-surface-variant",
        ),
        rx.el.h2(
            "Cuadro no disponible",
            class_name="text-headline-lg text-on-surface text-center w-full",
        ),
        rx.el.p(
            "Crea un torneo desde la home para ver el cuadro aquí.",
            class_name=(
                "w-full max-w-md mx-auto text-center text-body-md "
                "text-on-surface-variant"
            ),
        ),
        rx.link(
            rx.el.button(
                "Crear torneo",
                class_name=(
                    "bg-primary-container text-on-primary-fixed rounded-md "
                    "px-md py-sm text-label-bold min-h-[48px] "
                    "hover:opacity-90 transition-opacity"
                ),
            ),
            href="/tournament-config?type=tournament",
        ),
        class_name=(
            "w-full flex flex-col items-center justify-center gap-sm "
            "py-lg px-md "
            "bg-surface-container-lowest rounded-md "
            "border border-surface-container-highest "
            "shadow-[0_2px_10px_-4px_rgba(31,41,55,0.04)]"
        ),
    )


# ============================ Page ============================

def tournament_dashboard() -> rx.Component:
    return rx.box(
        _top_bar(),
        rx.el.main(
            rx.box(
                rx.box(
                    rx.el.h1(
                        TournamentState.tournament_name,
                        class_name="text-headline-xl text-on-surface",
                    ),
                    rx.cond(
                        TournamentState.has_tournament,
                        edit_players_button(
                            TournamentState.tournament_id, "tournament"
                        ),
                        rx.fragment(),
                    ),
                    class_name="flex items-center justify-center gap-xs mb-xs",
                ),
                rx.el.p(
                    TournamentState.tournament_subtitle,
                    class_name="text-body-md text-secondary",
                ),
                class_name="mb-lg text-center w-full",
            ),
            rx.cond(
                TournamentState.has_tournament,
                rx.box(
                    rx.foreach(TournamentState.bracket_columns, _column),
                    class_name=(
                        "min-w-[800px] flex items-stretch gap-xl py-lg relative"
                    ),
                    # Altura mínima proporcional al nº de matches de Ronda 1
                    # → asegura que `flex-1` en wrappers tenga espacio real.
                    style={"minHeight": TournamentState.bracket_min_height},
                ),
                _empty_state(),
            ),
            class_name=(
                "flex-1 w-full max-w-7xl mx-auto p-container-padding md:p-lg "
                "overflow-x-auto"
            ),
        ),
        bottom_nav(),
        edit_players_dialog(),
        class_name=(
            "bg-surface text-on-surface text-body-md min-h-screen "
            "flex flex-col pb-24 md:pb-0 font-sans"
        ),
    )
