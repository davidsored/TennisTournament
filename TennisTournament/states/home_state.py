"""Estado de la página principal (home)."""

from __future__ import annotations

import reflex as rx

from .league_state import LeagueState, STATUS_FINALIZADO


class HomeState(rx.State):
    """State del dashboard: tabs y agregación de competiciones recientes."""

    # Tab activo en la BottomNavBar (mobile): "home" | "history".
    active_tab: str = "home"

    # Listado dinámico de competiciones recientes (Liga / Torneo).
    # Se rellena en `setup_home` consultando `LeagueState` (≈ DB de la app).
    # Cada item contiene: title, subtitle, icon, status, tone, href.
    recent_competitions: list[dict[str, str]] = []

    # ---------------- Lifecycle ----------------

    async def setup_home(self):
        """Recolecta TODAS las competiciones desde `LeagueState` y las prepara para la UI.

        Itera sobre `LeagueState.competitions` (cada entrada = una competición
        única identificada por su `id`) y arma un dict por competición con la
        info que consume `recent_item`: título, subtítulo con nº de jugadores,
        icono temático, pill de estado (Activa/Finalizada) y href con `?id=…`
        para que el dashboard cargue la correcta.
        """
        items: list[dict[str, str]] = []

        league = await self.get_state(LeagueState)
        for comp in league.competitions:
            total = len(comp.matches)
            finalizados = sum(
                1 for m in comp.matches if m.status == STATUS_FINALIZADO
            )
            is_active = total > 0 and finalizados < total

            unique_players = len({p for p in comp.players if p.strip()})
            is_tournament = comp.competition_type == "tournament"
            type_label = "Eliminatoria" if is_tournament else "Round Robin"
            icon = "emoji_events" if is_tournament else "leaderboard"
            target = (
                f"/tournament-dashboard?id={comp.id}"
                if is_tournament
                else f"/league-dashboard?id={comp.id}"
            )
            items.append(
                {
                    "title": comp.name or "Competición sin nombre",
                    "subtitle": f"{type_label} • {unique_players} jugadores",
                    "icon": icon,
                    "status": "Activa" if is_active else "Finalizada",
                    "tone": "active" if is_active else "scheduled",
                    "href": target,
                }
            )

        # Más recientes primero (orden inverso al de creación).
        self.recent_competitions = list(reversed(items))

    # ---------------- Computed ----------------

    @rx.var
    def has_competitions(self) -> bool:
        return len(self.recent_competitions) > 0

    # ---------------- Event handlers ----------------

    def select_tab(self, tab: str) -> None:
        self.active_tab = tab
