"""Estado de la página principal (home)."""

from __future__ import annotations

import reflex as rx


class HomeState(rx.State):
    """State del dashboard: competiciones recientes y nav inferior activo."""

    # Tab activo en la BottomNavBar (mobile): "home" | "history".
    active_tab: str = "home"

    # Listado de competiciones recientes que alimenta la sección "Recent".
    # `tone` decide el color de la pill: "active" (tertiary) o "scheduled" (variant).
    recent_competitions: list[dict[str, str]] = [
        {
            "title": "Liga Primavera Sur",
            "subtitle": "Round Robin • 12 Jugadores",
            "icon": "sports_tennis",
            "status": "Activa",
            "tone": "active",
        },
        {
            "title": "Copa Master 2024",
            "subtitle": "Eliminatoria • 32 Jugadores",
            "icon": "emoji_events",
            "status": "Programada",
            "tone": "scheduled",
        },
    ]

    def select_tab(self, tab: str) -> None:
        self.active_tab = tab
