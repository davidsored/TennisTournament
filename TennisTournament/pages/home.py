"""CourtManager — Home / Dashboard.

Réplica del blueprint Stitch: TopAppBar, bento grid (Liga / Torneo),
sección de competiciones recientes (dinámica) y BottomNavBar mobile.
"""

from __future__ import annotations

import reflex as rx

from ..components.bento_card import bento_card
from ..components.bottom_nav import bottom_nav
from ..components.material_icon import material_icon
from ..components.recent_item import recent_item
from ..components.top_bar import top_bar
from ..states.home_state import HomeState


def _bento_grid() -> rx.Component:
    return rx.el.section(
        bento_card(
            title="Crear Liga",
            subtitle="(Round Robin)",
            icon="format_list_numbered",
            href="/tournament-config?type=league",
        ),
        bento_card(
            title="Crear Torneo",
            subtitle="(Eliminatoria)",
            icon="emoji_events",
            href="/tournament-config?type=tournament",
        ),
        class_name="grid grid-cols-1 md:grid-cols-2 gap-sm",
    )


def _empty_recent() -> rx.Component:
    """Estado vacío de la sección Recent: invita a crear la primera competición."""
    return rx.el.div(
        material_icon(
            "leaderboard",
            class_name="text-5xl text-on-surface-variant",
        ),
        rx.el.h4(
            "Aún no tienes competiciones",
            class_name="w-full text-label-bold text-on-surface text-center",
        ),
        rx.el.p(
            "Crea tu primera liga o torneo para verla aparecer aquí.",
            class_name=(
                "w-full max-w-md mx-auto text-center text-body-md "
                "text-on-surface-variant whitespace-normal"
            ),
        ),
        rx.link(
            rx.el.button(
                "Crear competición",
                class_name=(
                    "bg-primary-container text-on-primary-fixed rounded-md "
                    "px-md py-sm text-label-bold min-h-[48px] "
                    "hover:opacity-90 transition-opacity"
                ),
            ),
            href="/tournament-config?type=league",
        ),
        class_name=(
            "w-full flex flex-col items-center justify-center gap-sm "
            "py-lg px-md "
            "bg-surface-container-lowest rounded-md "
            "border border-surface-container-highest "
            "shadow-[0_2px_10px_-4px_rgba(31,41,55,0.04)]"
        ),
    )


def _recent_competitions() -> rx.Component:
    return rx.el.section(
        rx.el.h3(
            "Competiciones Recientes",
            class_name="text-headline-lg text-on-surface",
        ),
        rx.cond(
            HomeState.has_competitions,
            rx.box(
                rx.foreach(HomeState.recent_competitions, recent_item),
                class_name="grid grid-cols-1 gap-base",
            ),
            _empty_recent(),
        ),
        class_name="flex flex-col gap-sm mt-md",
    )


def home() -> rx.Component:
    return rx.box(
        top_bar(),
        rx.el.main(
            _bento_grid(),
            _recent_competitions(),
            class_name=(
                "p-container-padding md:p-lg max-w-4xl mx-auto flex flex-col gap-lg"
            ),
        ),
        bottom_nav(),
        class_name=(
            "bg-background text-on-background text-body-md antialiased "
            "min-h-screen pb-32 font-sans"
        ),
    )
