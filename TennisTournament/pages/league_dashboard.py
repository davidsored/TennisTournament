"""League Dashboard — clasificación + fixtures agrupados por ronda (Ida / Vuelta)."""

from __future__ import annotations

import reflex as rx

from ..components.bottom_nav import bottom_nav
from ..components.material_icon import material_icon
from ..states.league_state import LeagueState


# ============================ Top bars ============================
# Limpieza pedida: sin avatar, sin History, sin Settings. Título central = league_name.

def _home_button() -> rx.Component:
    """Botón con icono de casa que sale de la liga y vuelve a la home."""
    return rx.link(
        rx.el.button(
            material_icon("home", fill=True, class_name="text-2xl"),
            aria_label="Volver a Home",
            class_name=(
                "w-10 h-10 flex items-center justify-center text-primary "
                "hover:bg-surface-container active:bg-surface-container-high "
                "transition-colors rounded-full"
            ),
        ),
        href="/",
    )


def _desktop_top_bar() -> rx.Component:
    return rx.el.header(
        rx.box(
            _home_button(),
            rx.el.span(
                LeagueState.league_name,
                class_name=(
                    "text-headline-lg text-on-surface tracking-tight text-center flex-1"
                ),
            ),
            rx.box(class_name="w-10"),  # spacer simétrico para mantener el título centrado
            class_name=(
                "flex justify-between items-center px-4 h-16 w-full max-w-7xl mx-auto"
            ),
        ),
        class_name=(
            "border-b border-surface-container shadow-[0_2px_15px_-3px_rgba(31,41,55,0.04)] "
            "bg-surface-container-lowest tracking-tight sticky top-0 z-40 hidden md:flex"
        ),
    )


def _mobile_header() -> rx.Component:
    return rx.el.header(
        _home_button(),
        rx.el.h1(
            LeagueState.league_name,
            class_name=(
                "text-headline-lg text-on-surface tracking-tight text-center flex-1"
            ),
        ),
        rx.box(class_name="w-10"),  # spacer simétrico
        class_name=(
            "md:hidden sticky top-0 z-40 bg-surface-container-lowest/90 "
            "backdrop-blur-md px-container-padding py-sm flex items-center "
            "justify-between shadow-sm"
        ),
    )


# =========================== Standings ===========================

def _standings_header() -> rx.Component:
    th = "p-4 text-center text-label-bold uppercase tracking-wider"
    return rx.el.thead(
        rx.el.tr(
            rx.el.th("Pos", class_name=f"{th} w-12"),
            rx.el.th(
                "Player",
                class_name="p-4 text-label-bold uppercase tracking-wider text-left",
            ),
            rx.el.th("PJ", class_name=f"{th} w-16"),
            rx.el.th("PG", class_name=f"{th} w-16"),
            rx.el.th("PP", class_name=f"{th} w-16"),
            rx.el.th("Sets", class_name=f"{th} w-24"),
            rx.el.th(
                "Pts",
                class_name=f"{th} w-20 bg-primary/5 text-primary",
            ),
            class_name=(
                "bg-surface-container-low border-b border-surface-variant "
                "text-on-surface-variant"
            ),
        ),
    )


def _standings_row(row) -> rx.Component:
    td_center = "p-4 text-center text-on-surface-variant"
    return rx.el.tr(
        rx.el.td(row["pos"], class_name="p-4 text-center font-bold text-on-surface"),
        rx.el.td(
            row["player"],
            class_name="p-4 text-label-bold text-on-surface flex items-center gap-3",
        ),
        rx.el.td(row["pj"], class_name=td_center),
        rx.el.td(row["pg"], class_name=td_center),
        rx.el.td(row["pp"], class_name=td_center),
        rx.el.td(row["sets"], class_name=td_center),
        rx.el.td(
            row["pts"],
            class_name="p-4 text-center font-bold text-on-surface bg-primary/5",
        ),
        class_name=(
            "border-b border-surface-variant hover:bg-surface-container/50 "
            "transition-colors"
        ),
    )


def _standings_section() -> rx.Component:
    return rx.el.section(
        rx.el.h2("Standings", class_name="text-headline-lg text-on-surface"),
        rx.box(
            rx.box(
                rx.el.table(
                    _standings_header(),
                    rx.el.tbody(
                        rx.foreach(LeagueState.standings, _standings_row),
                        class_name="text-body-md",
                    ),
                    class_name="w-full text-left border-collapse min-w-[600px]",
                ),
                class_name="overflow-x-auto",
            ),
            class_name=(
                "bg-surface-container-lowest rounded-md "
                "shadow-[0_4px_24px_-8px_rgba(31,41,55,0.08)] overflow-hidden "
                "border border-surface-variant"
            ),
        ),
        class_name="flex flex-col gap-sm",
    )


# ============================ Fixtures ============================

def _player_line(name, value, is_winner: bool) -> rx.Component:
    return rx.box(
        rx.el.span(
            name,
            class_name=rx.cond(
                is_winner,
                "text-label-bold text-on-surface font-bold",
                "text-label-bold text-on-surface",
            ),
        ),
        rx.box(
            rx.el.span(
                value,
                class_name=rx.cond(
                    is_winner,
                    "w-8 text-center text-on-surface font-bold",
                    "w-8 text-center text-on-surface-variant",
                ),
            ),
            class_name="flex gap-2 text-score-display",
        ),
        class_name="flex items-center justify-between",
    )


def _status_badge(status) -> rx.Component:
    return rx.cond(
        status == "En curso",
        rx.box(
            "Live",
            class_name=(
                "absolute top-0 right-0 bg-primary/10 text-primary "
                "text-label-bold text-[10px] uppercase px-3 py-1 rounded-bl-md"
            ),
        ),
        rx.cond(
            status == "Finalizado",
            rx.box(
                "Final",
                class_name=(
                    "absolute top-0 right-0 bg-surface-container "
                    "text-on-surface-variant text-label-bold text-[10px] "
                    "uppercase px-3 py-1 rounded-bl-md"
                ),
            ),
            rx.box(
                "Pendiente",
                class_name=(
                    "absolute top-0 right-0 bg-surface-container "
                    "text-on-surface-variant text-label-bold text-[10px] "
                    "uppercase px-3 py-1 rounded-bl-md"
                ),
            ),
        ),
    )


def _fixture_card(
    leg_label: str,
    match_id,
    home,
    away,
    status,
    sets_home,
    sets_away,
    home_winner,
    away_winner,
) -> rx.Component:
    is_finished = status == "Finalizado"
    is_live = status == "En curso"

    base = (
        "bg-surface-container-lowest rounded-md "
        "shadow-[0_4px_24px_-8px_rgba(31,41,55,0.08)] "
        "p-md flex flex-col gap-md relative overflow-hidden"
    )
    accented = base + " border-l-4 border-l-primary"
    finished = base + " border border-surface-variant opacity-80"
    pending = base + " border border-surface-variant"

    return rx.box(
        _status_badge(status),
        rx.box(
            rx.el.span(
                leg_label,
                class_name=(
                    "text-on-surface-variant text-[12px] uppercase tracking-wider"
                ),
            ),
            class_name="flex justify-between items-center",
        ),
        rx.box(
            _player_line(home, sets_home, home_winner),
            rx.box(class_name="w-full h-px bg-surface-variant"),
            _player_line(away, sets_away, away_winner),
            class_name="flex flex-col gap-3",
        ),
        rx.cond(
            is_finished,
            rx.fragment(),
            rx.link(
                rx.el.button(
                    rx.cond(is_live, "Continuar partido", "Jugar partido"),
                    class_name=(
                        "w-full mt-2 bg-primary-container text-on-primary-fixed "
                        "rounded text-label-bold py-2 hover:opacity-90 "
                        "transition-opacity"
                    ),
                ),
                href=f"/scoreboard?match_id={match_id}",
                class_name="block",
            ),
        ),
        class_name=rx.cond(is_live, accented, rx.cond(is_finished, finished, pending)),
    )


def _ida_slot(pair) -> rx.Component:
    return rx.cond(
        pair.has_ida,
        _fixture_card(
            "Ida",
            pair.ida_id,
            pair.ida_home,
            pair.ida_away,
            pair.ida_status,
            pair.ida_sets_home,
            pair.ida_sets_away,
            pair.ida_home_winner,
            pair.ida_away_winner,
        ),
        rx.box(class_name="hidden md:block"),
    )


def _vuelta_slot(pair) -> rx.Component:
    return rx.cond(
        pair.has_vuelta,
        _fixture_card(
            "Vuelta",
            pair.vuelta_id,
            pair.vuelta_home,
            pair.vuelta_away,
            pair.vuelta_status,
            pair.vuelta_sets_home,
            pair.vuelta_sets_away,
            pair.vuelta_home_winner,
            pair.vuelta_away_winner,
        ),
        rx.box(class_name="hidden md:block"),
    )


def _round_section(rv) -> rx.Component:
    return rx.el.section(
        rx.box(
            rx.el.h3(rv.label, class_name="text-headline-lg text-on-surface"),
            rx.box(
                rx.el.span(
                    "Ida",
                    class_name=(
                        "flex-1 text-label-bold uppercase tracking-wider "
                        "text-on-surface-variant"
                    ),
                ),
                rx.el.span(
                    "Vuelta",
                    class_name=(
                        "flex-1 text-label-bold uppercase tracking-wider "
                        "text-on-surface-variant text-right"
                    ),
                ),
                class_name="hidden md:flex gap-md mt-xs",
            ),
        ),
        rx.box(
            rx.foreach(
                rv.pairs,
                lambda pair: rx.fragment(_ida_slot(pair), _vuelta_slot(pair)),
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-md mt-sm",
        ),
        class_name="flex flex-col gap-xs",
    )


def _fixtures_section() -> rx.Component:
    return rx.el.section(
        rx.box(
            rx.el.h2(
                rx.el.span("Fixtures"),
                rx.el.span(
                    "Ida y Vuelta",
                    class_name="text-on-surface-variant text-body-md ml-2",
                ),
                class_name="text-headline-lg text-on-surface",
            ),
            class_name="flex justify-between items-end",
        ),
        rx.box(
            rx.foreach(LeagueState.grouped_fixtures, _round_section),
            class_name="flex flex-col gap-lg",
        ),
        class_name="flex flex-col gap-sm",
    )


# =========================== Empty state ===========================

def _empty_state() -> rx.Component:
    return rx.box(
        material_icon(
            "sports_tennis", class_name="text-6xl text-on-surface-variant"
        ),
        rx.el.h2(
            "Aún no has creado una liga",
            class_name="text-headline-lg text-on-surface text-center",
        ),
        rx.el.p(
            "Vuelve a la home y crea una nueva liga para ver aquí la clasificación.",
            class_name="text-body-md text-on-surface-variant text-center max-w-md",
        ),
        rx.link(
            rx.el.button(
                "Crear liga",
                class_name=(
                    "bg-primary-container text-on-primary-fixed rounded-md "
                    "px-md py-sm text-label-bold min-h-[48px] "
                    "hover:opacity-90 transition-opacity"
                ),
            ),
            href="/tournament-config?type=league",
        ),
        class_name=(
            "flex flex-col items-center gap-md py-lg "
            "bg-surface-container-lowest rounded-md "
            "border border-surface-variant"
        ),
    )


# ============================== Page ==============================

def league_dashboard() -> rx.Component:
    return rx.box(
        _desktop_top_bar(),
        _mobile_header(),
        rx.el.main(
            rx.cond(
                LeagueState.has_league,
                rx.box(
                    _standings_section(),
                    _fixtures_section(),
                    class_name="flex flex-col gap-xl",
                ),
                _empty_state(),
            ),
            class_name=(
                "flex-1 w-full max-w-7xl mx-auto px-container-padding py-md md:py-lg "
                "flex flex-col gap-xl"
            ),
        ),
        bottom_nav(),
        class_name=(
            "bg-surface text-on-surface text-body-md min-h-screen "
            "flex flex-col pb-24 md:pb-0 font-sans"
        ),
    )
