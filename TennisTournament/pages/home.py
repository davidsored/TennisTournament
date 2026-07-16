"""CourtManager — Home / Dashboard.

Réplica del blueprint Stitch: TopAppBar, bento grid (Liga / Torneo),
sección de competiciones recientes (dinámica) y BottomNavBar mobile.
Incluye disparador de modo administrador (clave secreta vía ADMIN_KEY).
"""

from __future__ import annotations

import reflex as rx

from ..components.bento_card import bento_card
from ..components.bottom_nav import bottom_nav
from ..components.dialog_style import DIALOG_CONTENT_STYLE
from ..components.material_icon import material_icon
from ..components.recent_item import recent_item
from ..components.top_bar import top_bar
from ..states.admin_state import AdminState
from ..states.home_state import HomeState


# ============================ Bento ============================

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
        bento_card(
            title="Partido Amistoso",
            subtitle="(Sin competición)",
            icon="sports_tennis",
            href="/casual-match",
        ),
        class_name="grid grid-cols-1 md:grid-cols-3 gap-sm",
    )


# ============================ Empty Recent ============================

def _empty_recent() -> rx.Component:
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
                "w-full text-center text-body-md "
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


# ============================ Recent ============================

def _recent_competitions() -> rx.Component:
    return rx.el.section(
        rx.box(
            rx.el.h3(
                "Competiciones Recientes",
                class_name="text-headline-lg text-on-surface",
            ),
            _admin_trigger(),
            class_name="flex items-center justify-between",
        ),
        rx.box(
            rx.cond(
                HomeState.has_competitions,
                rx.box(
                    rx.foreach(HomeState.recent_competitions, recent_item),
                    class_name="grid grid-cols-1 gap-base w-full", 
                ),
                _empty_recent(),
            ),
            width="100%", 
        ),
        class_name="flex flex-col gap-sm mt-md",
    )


# ============================ Admin ============================

def _admin_trigger() -> rx.Component:
    """Pequeño icono que abre el diálogo de modo administrador."""
    return rx.el.button(
        rx.cond(
            AdminState.is_admin,
            material_icon(
                "admin_panel_settings",
                fill=True,
                class_name="text-primary text-2xl",
            ),
            material_icon(
                "lock",
                class_name="text-on-surface-variant text-xl",
            ),
        ),
        on_click=AdminState.open_dialog,
        aria_label="Modo administrador",
        class_name=(
            "w-10 h-10 flex items-center justify-center rounded-full "
            "hover:bg-surface-container active:bg-surface-container-high "
            "transition-colors"
        ),
    )


def _admin_dialog_unauth() -> rx.Component:
    return rx.box(
        rx.el.p(
            "Introduce la clave para desbloquear las acciones de administrador.",
            class_name="text-body-md text-on-surface-variant mb-sm",
        ),
        rx.el.input(
            placeholder="Clave",
            type="password",
            value=AdminState.key_input,
            on_change=AdminState.set_key_input,
            class_name=(
                "w-full bg-surface-container-lowest border border-outline-variant "
                "rounded min-h-[48px] px-sm py-xs "
                "focus:outline-none focus:border-primary-container "
                "focus:ring-2 focus:ring-primary-container/20 transition-colors "
                "text-on-surface text-body-md placeholder:text-outline"
            ),
        ),
        rx.cond(
            AdminState.error_message != "",
            rx.el.p(
                AdminState.error_message,
                class_name="text-error text-sm mt-xs",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.dialog.close(
                rx.el.button(
                    "Cancelar",
                    class_name=(
                        "px-md py-sm rounded text-label-bold "
                        "text-on-surface-variant hover:bg-surface-container "
                        "transition-colors"
                    ),
                ),
            ),
            rx.el.button(
                "Validar",
                on_click=AdminState.check_admin_key,
                class_name=(
                    "px-md py-sm rounded bg-primary-container "
                    "text-on-primary-fixed text-label-bold "
                    "hover:opacity-90 transition-opacity"
                ),
            ),
            class_name="flex justify-end gap-sm mt-md",
        ),
        class_name="flex flex-col w-full",
        width="100%",
    )


def _admin_dialog_authed() -> rx.Component:
    return rx.box(
        rx.el.p(
            "Las acciones de administrador (papelera) están disponibles en cada competición del listado.",
            class_name="text-body-md text-on-surface-variant mb-md",
        ),
        rx.el.button(
            material_icon("logout", class_name="text-xl"),
            rx.el.span("Salir del modo admin", class_name="text-label-bold"),
            on_click=AdminState.logout_admin,
            class_name=(
                "w-full bg-error-container text-on-error-container "
                "rounded-md px-md py-sm flex items-center justify-center gap-xs "
                "min-h-[48px] hover:opacity-90 transition-opacity"
            ),
        ),
        class_name="flex flex-col gap-sm",
    )


def _admin_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    AdminState.is_admin,
                    "Modo administrador activo",
                    "Modo administrador",
                ),
                class_name="text-headline-lg text-on-surface mb-xs",
            ),
            rx.cond(
                AdminState.is_admin,
                _admin_dialog_authed(),
                _admin_dialog_unauth(),
            ),
            style=DIALOG_CONTENT_STYLE,
        ),
        open=AdminState.dialog_open,
        on_open_change=AdminState.set_dialog_open,
    )


# ============================ Page ============================

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
        _admin_dialog(),
        class_name=(
            "bg-background text-on-background text-body-md antialiased "
            "min-h-screen pb-32 font-sans"
        ),
    )
