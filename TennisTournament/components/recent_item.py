"""Item de la lista "Competiciones Recientes" con pill de estado."""

from __future__ import annotations

import reflex as rx

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
                "bg-surface-variant text-on-surface-variant px-3 py-1 "
                "rounded-full text-xs text-label-bold tracking-wide"
            ),
        ),
    )


def recent_item(comp) -> rx.Component:
    """Renderiza una competición reciente.

    `comp` es un dict reactivo con: title, subtitle, icon, status, tone.
    """
    return rx.box(
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
        _status_pill(comp["status"], comp["tone"]),
        class_name=(
            "bg-surface-container-lowest rounded-md p-sm "
            "flex items-center justify-between "
            "border border-surface-container-highest "
            "shadow-[0_2px_10px_-4px_rgba(31,41,55,0.04)] "
            "cursor-pointer hover:bg-surface-container-low transition-colors"
        ),
    )
