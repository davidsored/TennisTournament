"""Estado del formulario de "Partido Amistoso".

Recoge los nombres de los dos jugadores y el formato del partido. El estado
real del marcador se carga en `ScoreboardState` desde los query params de la
URL para que un refresco no pierda los datos del partido.
"""

from __future__ import annotations

from urllib.parse import quote

import reflex as rx


class CasualMatchState(rx.State):
    """Formulario para iniciar un partido directo sin liga ni torneo."""

    player_j1: str = ""
    player_j2: str = ""
    sets_per_match: int = 3
    games_per_set: int = 6

    # ---------------- Lifecycle ----------------

    def setup_page(self) -> None:
        self.player_j1 = ""
        self.player_j2 = ""
        self.sets_per_match = 3
        self.games_per_set = 6

    # ---------------- Inputs ----------------

    def set_player_j1(self, value: str) -> None:
        self.player_j1 = value

    def set_player_j2(self, value: str) -> None:
        self.player_j2 = value

    # ---------------- Steppers ----------------
    # Sets: solo valores impares (1, 3, 5, 7, 9) para evitar empates en el
    # resultado final. Misma regla que el formulario de competiciones.

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

    # ---------------- Acción ----------------

    def start_match(self):
        p1 = self.player_j1.strip()
        p2 = self.player_j2.strip()
        if not p1 or not p2:
            return rx.toast.error("Introduce el nombre de ambos jugadores")
        if p1.lower() == p2.lower():
            return rx.toast.error("Los nombres de los jugadores deben ser distintos")

        # La configuración viaja en la URL: si el usuario refresca el marcador,
        # ScoreboardState la vuelve a leer y mantiene la sesión coherente.
        url = (
            f"/scoreboard?casual=1"
            f"&p1={quote(p1)}&p2={quote(p2)}"
            f"&sets={self.sets_per_match}&games={self.games_per_set}"
        )
        return rx.redirect(url)
