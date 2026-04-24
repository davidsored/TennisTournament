"""Estado del marcador en vivo."""

from __future__ import annotations

import reflex as rx


class ScoreboardState(rx.State):
    player_a: str = "Jugador A"
    player_b: str = "Jugador B"

    points_a: int = 0
    points_b: int = 0
    games_a: int = 0
    games_b: int = 0
    sets_a: int = 0
    sets_b: int = 0

    in_tiebreak: bool = False
    match_over: bool = False

    def point_a(self) -> None:
        """Suma un punto al jugador A (implementar lógica de tenis)."""

    def point_b(self) -> None:
        """Suma un punto al jugador B (implementar lógica de tenis)."""

    def reset_match(self) -> None:
        self.points_a = self.points_b = 0
        self.games_a = self.games_b = 0
        self.sets_a = self.sets_b = 0
        self.in_tiebreak = False
        self.match_over = False
