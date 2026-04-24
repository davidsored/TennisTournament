"""Estado de la vista de ligas."""

from __future__ import annotations

import reflex as rx


class LeagueState(rx.State):
    league_name: str = ""
    players: list[str] = []

    def add_player(self, name: str) -> None:
        if name and name not in self.players:
            self.players.append(name)

    def remove_player(self, name: str) -> None:
        if name in self.players:
            self.players.remove(name)

    def generate_fixture(self) -> None:
        """Dispara la generación Round Robin x2 sobre el modelo League."""
