"""Live Match Editor — UI completa del marcador en vivo.

Traducción a Reflex de la plantilla Tailwind/Stitch usando los tokens del
sistema "Advantage" (DESIGN.md). Toda la lógica de puntuación vive en
`models/match.py`; aquí solo se renderizan los datos del `ScoreboardState`.
"""

from __future__ import annotations

import reflex as rx

from ..states.scoreboard_state import ScoreboardState


# ============================ Header ============================

def _status_pills() -> rx.Component:
    return rx.el.div(
        rx.el.span(
            ScoreboardState.estado_label,
            class_name=(
                "inline-flex items-center px-3 py-1 rounded-full bg-primary-container "
                "text-on-primary-container text-label-bold tracking-wide uppercase shadow-sm"
            ),
        ),
        rx.el.span(
            ScoreboardState.current_set_label,
            class_name=(
                "inline-flex items-center px-2 py-1 rounded-full bg-surface-variant "
                "text-on-surface-variant text-label-bold uppercase tracking-wider"
            ),
        ),
        class_name="flex items-center gap-2",
    )


def _header_section() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            _status_pills(),
            rx.el.h1(
                ScoreboardState.match_title,
                class_name="text-headline-lg text-on-surface tracking-tight mt-1",
            ),
            rx.el.p(
                ScoreboardState.match_subtitle,
                class_name="text-body-md text-secondary",
            ),
            class_name="flex flex-col gap-1",
        ),
        rx.el.button(
            rx.icon("settings", size=22),
            aria_label="Ajustes del partido",
            class_name=(
                "p-2 rounded-full text-secondary hover:bg-surface-container "
                "active:bg-surface-container-high transition-colors"
            ),
        ),
        class_name=(
            "px-container-padding pt-md pb-sm flex justify-between items-start shrink-0"
        ),
    )


# ========================= Score table ==========================

def _table_header() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            "Jugador",
            class_name=(
                "flex-1 text-label-bold text-secondary uppercase tracking-wider "
                "text-xs flex items-center"
            ),
        ),
        rx.el.div(
            rx.foreach(
                ScoreboardState.set_labels,
                lambda label: rx.el.div(
                    label,
                    class_name="w-6 text-center text-label-bold text-secondary text-xs",
                ),
            ),
            class_name="flex gap-4 pr-6",
        ),
        rx.el.div(
            "Juego",
            class_name=(
                "w-12 text-center text-label-bold text-on-surface uppercase "
                "tracking-wider text-xs border-l border-surface-container pl-2"
            ),
        ),
        rx.el.div(
            "Punto",
            class_name=(
                "w-16 text-center text-label-bold text-primary tracking-wider "
                "text-xs border-l border-surface-container pl-2 uppercase"
            ),
        ),
        class_name=(
            "flex bg-surface-container-low px-4 py-2 border-b border-surface-container"
        ),
    )


def _set_cell(s) -> rx.Component:
    return rx.el.div(
        s["mine"],
        class_name=rx.cond(
            s["mine"] > s["opp"],
            "w-6 text-center text-body-lg text-on-surface font-semibold",
            "w-6 text-center text-body-lg text-secondary",
        ),
    )


def _player_row(
    name,
    set_view,
    games,
    point_visual,
    is_server,
    is_last_row: bool = False,
) -> rx.Component:
    point_text_class = rx.cond(
        is_server,
        "text-score-display text-inverse-primary text-2xl tracking-normal",
        "text-score-display text-inverse-on-surface text-2xl tracking-normal",
    )
    server_dot = rx.cond(
        is_server,
        rx.el.span(class_name="w-3 h-3 rounded-full bg-primary-container shrink-0"),
        rx.el.span(class_name="w-3 h-3 shrink-0"),
    )
    server_bar = rx.cond(
        is_server,
        rx.el.div(
            class_name=(
                "absolute left-0 top-0 bottom-0 w-1 bg-primary-container "
                "rounded-r-full"
            ),
        ),
        rx.fragment(),
    )

    base = (
        "flex items-center px-4 py-3 bg-surface-container-lowest relative"
    )
    if not is_last_row:
        base += " border-b border-surface-container"

    return rx.el.div(
        server_bar,
        # Jugador
        rx.el.div(
            server_dot,
            rx.el.span(
                name,
                class_name="text-headline-lg text-on-surface truncate",
            ),
            class_name="flex-1 flex items-center gap-2",
        ),
        # Sets pasados
        rx.el.div(
            rx.foreach(set_view, _set_cell),
            class_name="flex gap-4 pr-6",
        ),
        # Juego actual
        rx.el.div(
            games,
            class_name=(
                "w-12 text-center text-headline-xl text-on-surface "
                "border-l border-surface-container pl-2"
            ),
        ),
        # Bloque de punto (alto contraste)
        rx.el.div(
            rx.el.div(
                class_name=(
                    "absolute inset-0 bg-gradient-to-b from-white/10 to-transparent "
                    "pointer-events-none"
                ),
            ),
            rx.el.span(point_visual, class_name=point_text_class),
            class_name=(
                "w-16 h-12 ml-2 bg-inverse-surface rounded-lg flex items-center "
                "justify-center shadow-inner relative overflow-hidden"
            ),
        ),
        class_name=base,
    )


def _score_card() -> rx.Component:
    return rx.el.div(
        _table_header(),
        _player_row(
            ScoreboardState.player_j1,
            ScoreboardState.sets_view_j1,
            ScoreboardState.juegos_j1,
            ScoreboardState.score_visual_j1,
            ScoreboardState.is_server_j1,
            is_last_row=False,
        ),
        _player_row(
            ScoreboardState.player_j2,
            ScoreboardState.sets_view_j2,
            ScoreboardState.juegos_j2,
            ScoreboardState.score_visual_j2,
            ScoreboardState.is_server_j2,
            is_last_row=True,
        ),
        class_name=(
            "bg-surface-container-lowest rounded-xl "
            "shadow-[0_4px_24px_-8px_rgba(31,41,55,0.08)] overflow-hidden "
            "border border-surface-container flex flex-col"
        ),
    )


# ====================== Tiebreak indicator ======================

def _tiebreak_indicator() -> rx.Component:
    return rx.cond(
        ScoreboardState.is_tiebreak,
        rx.el.div(
            rx.icon("timer", size=14, class_name="text-on-primary-container"),
            rx.el.span(
                "Modo Tie-Break Activo",
                class_name=(
                    "text-label-bold text-on-primary-container uppercase "
                    "tracking-widest text-[10px]"
                ),
            ),
            class_name=(
                "flex items-center justify-center gap-2 px-3 py-1 rounded-full "
                "bg-primary-container/40 self-center"
            ),
        ),
        rx.el.div(
            rx.icon("timer", size=14, class_name="text-secondary"),
            rx.el.span(
                "Modo Tie-Break Inactivo",
                class_name=(
                    "text-label-bold text-secondary uppercase tracking-widest "
                    "text-[10px]"
                ),
            ),
            class_name="flex items-center justify-center gap-2 opacity-40",
        ),
    )


# ========================== Controles ===========================

def _point_button(player_name, on_click) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            player_name,
            class_name=(
                "text-headline-lg text-on-surface "
                "group-active:text-on-primary-container"
            ),
        ),
        rx.el.span(
            "+ Punto",
            class_name=(
                "text-label-bold text-secondary group-active:text-on-primary-container/80 "
                "uppercase tracking-widest text-xs bg-surface-container "
                "group-active:bg-primary/10 px-3 py-1 rounded-full"
            ),
        ),
        on_click=on_click,
        class_name=(
            "flex-1 bg-surface-container-lowest border-2 border-surface-container "
            "rounded-xl flex flex-col items-center justify-center gap-2 "
            "active:bg-primary-container active:border-primary-container "
            "transition-all duration-100 "
            "shadow-[0_2px_10px_-4px_rgba(31,41,55,0.04)] group "
            "disabled:opacity-40 disabled:cursor-not-allowed"
        ),
        disabled=ScoreboardState.is_finished,
    )


def _secondary_button(label: str, icon_tag, on_click=None, disabled=None) -> rx.Component:
    children = []
    if icon_tag is not None:
        children.append(rx.icon(icon_tag, size=18))
    children.append(rx.el.span(label, class_name="text-label-bold"))
    kwargs = {"on_click": on_click} if on_click is not None else {}
    if disabled is not None:
        kwargs["disabled"] = disabled
    return rx.el.button(
        *children,
        class_name=(
            "flex-1 bg-surface-container border border-surface-variant rounded-xl "
            "flex items-center justify-center gap-2 text-on-surface-variant "
            "hover:bg-surface-container-high active:bg-surface-dim transition-colors "
            "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-surface-container"
        ),
        **kwargs,
    )


def _judge_controls() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            _point_button(ScoreboardState.player_j1, ScoreboardState.sumar_punto(1)),
            _point_button(ScoreboardState.player_j2, ScoreboardState.sumar_punto(2)),
            class_name="flex gap-gutter flex-1 min-h-[160px]",
        ),
        rx.el.div(
            _secondary_button(
                "Deshacer",
                "undo-2",
                on_click=ScoreboardState.undo_point,
                disabled=ScoreboardState.history.length() == 0,
            ),
            _secondary_button("Falta", "triangle-alert"),
            class_name="flex gap-gutter h-16",
        ),
        class_name="flex-1 flex flex-col gap-gutter mt-2",
    )


# ===================== Footer fijo (acción) =====================

def _finish_footer() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("flag", size=22),
            "Finalizar partido",
            on_click=ScoreboardState.reset_match,
            class_name=(
                "w-full max-w-3xl bg-primary-container text-on-primary-container "
                "text-headline-lg py-4 rounded-xl flex justify-center items-center "
                "gap-3 shadow-lg active:scale-[0.98] transition-transform"
            ),
        ),
        class_name=(
            "fixed bottom-0 left-0 w-full p-container-padding bg-surface/95 "
            "backdrop-blur-md border-t border-surface-container z-50 "
            "flex justify-center"
        ),
    )


# =========================== Página ============================

def scoreboard() -> rx.Component:
    return rx.el.div(
        _header_section(),
        rx.el.main(
            _score_card(),
            _tiebreak_indicator(),
            _judge_controls(),
            class_name=(
                "flex-1 flex flex-col px-container-padding gap-md pb-32 "
                "max-w-3xl mx-auto w-full"
            ),
        ),
        _finish_footer(),
        class_name=(
            "bg-surface text-on-surface antialiased min-h-screen "
            "flex flex-col relative font-sans "
            "selection:bg-primary-container selection:text-on-primary-container"
        ),
    )
