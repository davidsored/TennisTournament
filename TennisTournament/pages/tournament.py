"""Página de torneo eliminatorio — estilo Advantage."""

from __future__ import annotations

import reflex as rx

from ..components.bracket import bracket
from ..components.navbar import navbar


def tournament() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.h1(
                "Torneo eliminatorio",
                class_name="text-headline-xl text-graphite mb-lg",
            ),
            bracket(),
            class_name="max-w-6xl mx-auto px-sm py-lg",
        ),
        class_name="min-h-screen bg-surface font-sans",
    )
