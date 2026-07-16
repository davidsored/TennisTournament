"""Item de la lista "Competiciones Recientes" con pill de estado y navegación."""

from __future__ import annotations

import reflex as rx

from ..states.admin_state import AdminState
from ..states.home_state import HomeState
from .material_icon import material_icon


def _status_pill(status, tone) -> rx.Component:
    """Pill que cambia de color según `tone` ('active' | 'scheduled')."""
    return rx.el.div(
        status,
        class_name=rx.cond(
            tone == "active",
            (
                "bg-tertiary-container text-on-tertiary-container px-3 py-1 "
                "rounded-full text-xs text-label-bold tracking-wide"
            ),
            (
                "bg-surface-container-highest text-on-surface-variant px-3 py-1 "
                "rounded-full text-xs text-label-bold tracking-wide"
            ),
        ),
    )


def _delete_button(comp_id, comp_type) -> rx.Component:
    """Papelera (solo visible en modo admin). Elimina la competición."""
    return rx.cond(
        AdminState.is_admin,
        rx.el.button(
            material_icon("delete", class_name="text-error text-xl"),
            on_click=HomeState.delete_competition(
                comp_id, comp_type
            ).stop_propagation,
            aria_label="Eliminar competición",
            class_name=(
                "w-9 h-9 rounded-full flex items-center justify-center "
                "hover:bg-error-container/40 active:bg-error-container/60 "
                "transition-colors"
            ),
        ),
        rx.fragment(),
    )


def recent_item(comp) -> rx.Component:
    """Renderiza una competición reciente (clicable) con acción admin opcional."""
    body_link = rx.link(
        rx.box(
            rx.box(
                material_icon(comp["icon"], class_name="text-primary text-2xl"),
                class_name=(
                    "w-12 h-12 rounded-md bg-surface-container flex items-center "
                    "justify-center text-primary border border-surface-variant"
                ),
            ),
            rx.box(
                rx.el.h4(
                    comp["title"],
                    class_name="text-label-bold text-on-surface",
                ),
                rx.el.p(
                    comp["subtitle"],
                    class_name="text-body-md text-on-surface-variant text-sm",
                ),
            ),
            class_name="flex items-center gap-sm",
        ),
        href=comp["href"],
        class_name="flex-1 block cursor-pointer",
    )

    return rx.box(
        body_link,
        rx.box(
            _status_pill(comp["status"], comp["tone"]),
            _delete_button(comp["id"], comp["type"]),
            class_name="flex items-center gap-xs",
        ),
        class_name=(
            "bg-surface-container-lowest rounded-md p-sm "
            "flex items-center justify-between "
            "border border-surface-container-highest "
            "shadow-[0_2px_10px_-4px_rgba(31,41,55,0.04)] "
            "hover:bg-surface-container-low transition-colors"
        ),
    )
