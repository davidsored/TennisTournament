"""Página de liga (Round Robin x2) — estilo Advantage."""

from __future__ import annotations

import reflex as rx

from ..components.navbar import navbar


def league() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.h1(
                "Liga · Round Robin x2",
                class_name="text-headline-xl text-graphite mb-lg",
            ),
            rx.el.div(
                rx.el.p(
                    "Aquí irán la tabla de posiciones y el calendario de la liga.",
                    class_name="text-body-md text-on-surface-variant",
                ),
                class_name=(
                    "p-lg rounded-xl bg-surface-container-lowest "
                    "border border-outline-variant shadow-card"
                ),
            ),
            class_name="max-w-6xl mx-auto px-sm py-lg",
        ),
        class_name="min-h-screen bg-surface font-sans",
    )
