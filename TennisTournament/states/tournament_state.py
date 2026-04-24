"""Estado de la vista de torneos eliminatorios."""

from __future__ import annotations

import reflex as rx


class TournamentState(rx.State):
    tournament_name: str = ""
    players: list[str] = []

    def add_player(self, name: str) -> None:
        if name and name not in self.players:
            self.players.append(name)

    def remove_player(self, name: str) -> None:
        if name in self.players:
            self.players.remove(name)

    def generate_bracket(self) -> None:
        """Dispara la generación del bracket eliminatorio."""
