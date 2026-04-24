"""Barra de navegación — tokens Advantage (superficie clara + pop Tennis Green)."""

from __future__ import annotations

import reflex as rx


def _link(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        class_name=(
            "px-sm py-xs rounded-lg text-label-bold text-on-surface "
            "hover:bg-surface-container transition-colors"
        ),
    )


def navbar() -> rx.Component:
    return rx.el.nav(
        rx.el.div(
            rx.el.a(
                rx.el.span(
                    "Advantage",
                    class_name="text-headline-lg text-graphite tracking-tight",
                ),
                href="/",
                class_name="flex items-center gap-xs",
            ),
            rx.el.div(
                _link("Inicio", "/"),
                _link("Marcador", "/scoreboard"),
                _link("Ligas", "/league"),
                _link("Torneos", "/tournament"),
                class_name="flex items-center gap-1",
            ),
            class_name="max-w-6xl mx-auto px-sm h-14 flex items-center justify-between",
        ),
        class_name=(
            "w-full bg-surface-container-lowest border-b border-outline-variant "
            "sticky top-0 z-10"
        ),
    )
