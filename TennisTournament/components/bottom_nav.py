"""BottomNavBar fija (solo mobile) con tabs Home / History."""

from __future__ import annotations

import reflex as rx

from ..states.home_state import HomeState
from .material_icon import material_icon


def _tab(label: str, icon: str, key: str, fill_when_active: bool = True) -> rx.Component:
    is_active = HomeState.active_tab == key
    return rx.el.button(
        rx.cond(
            is_active,
            material_icon(icon, fill=fill_when_active, class_name="mb-1 text-2xl"),
            material_icon(icon, class_name="mb-1 text-2xl"),
        ),
        rx.el.span(label),
        on_click=HomeState.select_tab(key),
        class_name=rx.cond(
            is_active,
            (
                "flex flex-col items-center justify-center "
                "text-on-primary-container bg-primary-container "
                "rounded-md px-6 py-1.5 active:scale-95 transition-transform duration-150"
            ),
            (
                "flex flex-col items-center justify-center text-on-surface-variant "
                "px-6 py-1.5 hover:text-on-surface transition-colors active:scale-95 "
                "transition-transform duration-150"
            ),
        ),
    )


def bottom_nav() -> rx.Component:
    return rx.el.nav(
        _tab("Home", "home", "home"),
        _tab("History", "history", "history", fill_when_active=False),
        class_name=(
            "md:hidden bg-surface-container-lowest/95 backdrop-blur-md "
            "text-[10px] font-semibold uppercase tracking-wider "
            "fixed bottom-0 left-0 w-full z-50 "
            "border-t border-surface-container-highest "
            "shadow-[0_-4px_20px_-4px_rgba(31,41,55,0.06)] "
            "flex justify-around items-center h-20 pb-safe px-8"
        ),
    )
