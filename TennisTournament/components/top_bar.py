"""TopAppBar (sticky) con título centrado y acciones laterales."""

from __future__ import annotations

import reflex as rx

from .material_icon import material_icon


def top_bar() -> rx.Component:
    return rx.el.header(        
        rx.box(
            "CourtManager",
            class_name=(
                "text-lg font-black text-on-surface uppercase tracking-widest "
                "text-center flex-1"
            ),
        ),        
        class_name=(
            "bg-surface-container-lowest text-body-lg tracking-tight top-0 "
            "border-b border-surface-container-highest "
            "shadow-[0_2px_15px_-3px_rgba(31,41,55,0.04)] "
            "flex justify-between items-center px-4 h-16 w-full sticky z-40"
        ),
    )
