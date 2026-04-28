"""Estado del formulario de configuración de torneo / liga."""

from __future__ import annotations

import reflex as rx


class ConfigState(rx.State):
    """Maneja los datos del formulario de creación de competición."""

    tournament_name: str = ""
    sets_per_match: int = 3
    games_per_set: int = 6
    players: list[str] = ["", ""]

    # ---------------- Lifecycle ----------------

    def setup_page(self) -> None:
        """Resetea el formulario a sus valores por defecto cada vez que se entra."""
        self.tournament_name = ""
        self.sets_per_match = 3
        self.games_per_set = 6
        self.players = ["", ""]

    # ---------------- Texto / inputs ----------------

    def set_tournament_name(self, value: str) -> None:
        self.tournament_name = value

    # ---------------- Steppers numéricos ----------------

    def increment_sets(self) -> None:
        if self.sets_per_match < 9:
            self.sets_per_match += 2 if self.sets_per_match in (1, 3, 5, 7) else 1

    def decrement_sets(self) -> None:
        if self.sets_per_match > 1:
            self.sets_per_match -= 2 if self.sets_per_match in (3, 5, 7, 9) else 1

    def increment_games(self) -> None:
        if self.games_per_set < 12:
            self.games_per_set += 1

    def decrement_games(self) -> None:
        if self.games_per_set > 1:
            self.games_per_set -= 1

    # ---------------- Lista dinámica de jugadores ----------------

    def add_player(self) -> None:
        self.players.append("")

    def remove_player(self, index: int) -> None:
        if 0 <= index < len(self.players):
            self.players.pop(index)

    def update_player(self, index: int, value: str) -> None:
        if 0 <= index < len(self.players):
            self.players[index] = value

    # ---------------- Computed ----------------

    @rx.var
    def registered_count(self) -> int:
        """Cantidad de jugadores con nombre no vacío (los "inscritos")."""
        return sum(1 for p in self.players if p.strip())

    @rx.var
    def registered_label(self) -> str:
        return f"{self.registered_count} inscritos"

    # ---------------- Acción guardar ----------------

    def save_config(self):
        print(
            "Configuración guardada:",
            {
                "name": self.tournament_name,
                "sets_per_match": self.sets_per_match,
                "games_per_set": self.games_per_set,
                "players": [p for p in self.players if p.strip()],
            },
        )
        return rx.redirect("/scoreboard")
