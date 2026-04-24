"""Componente de bracket eliminatorio (placeholder con estilo Advantage)."""

from __future__ import annotations

import reflex as rx


def bracket() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Bracket pendiente de implementación.",
            class_name="text-body-md text-on-surface-variant italic",
        ),
        class_name=(
            "w-full p-lg rounded-xl bg-surface-container-lowest "
            "border border-outline-variant shadow-card"
        ),
    )
