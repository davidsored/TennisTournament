"""Estado del formulario de configuración de torneo / liga."""

from __future__ import annotations

import reflex as rx

from ..logic.validation import validate_competition_config
from .league_state import LeagueState


COMPETITION_LEAGUE = "league"
COMPETITION_TOURNAMENT = "tournament"


class ConfigState(rx.State):
    """Maneja los datos del formulario de creación de competición."""

    competition_type: str = COMPETITION_TOURNAMENT  # "league" | "tournament"
    tournament_name: str = ""
    sets_per_match: int = 3
    games_per_set: int = 6
    players: list[str] = ["", ""]

    # ---------------- Lifecycle ----------------

    def setup_page(self) -> None:
        """Resetea el formulario y lee `?type=` de la URL al entrar en la página."""
        self.tournament_name = ""
        self.sets_per_match = 3
        self.games_per_set = 6
        self.players = ["", ""]
        type_param = self.router.page.params.get("type", COMPETITION_TOURNAMENT)
        self.competition_type = (
            COMPETITION_LEAGUE if type_param == COMPETITION_LEAGUE else COMPETITION_TOURNAMENT
        )

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
        return sum(1 for p in self.players if p.strip())

    @rx.var
    def registered_label(self) -> str:
        return f"{self.registered_count} inscritos"

    @rx.var
    def page_title(self) -> str:
        return (
            "Configuración de Liga"
            if self.competition_type == COMPETITION_LEAGUE
            else "Configuración de Torneo"
        )

    @rx.var
    def is_league(self) -> bool:
        return self.competition_type == COMPETITION_LEAGUE

    # ---------------- Acción guardar ----------------

    async def save_config(self):
        # Validación completa (nombre, nº jugadores, rangos, duplicados) con
        # feedback visual. Los mutadores repiten el chequeo server-side.
        name = self.tournament_name.strip()
        clean_players = [p for p in self.players if p.strip()]

        error = validate_competition_config(
            name, clean_players, self.sets_per_match, self.games_per_set
        )
        if error:
            return rx.toast.error(error)

        league = await self.get_state(LeagueState)

        if self.competition_type == COMPETITION_LEAGUE:
            league.setup_league(
                name=name,
                players=clean_players,
                sets_per_match=self.sets_per_match,
                games_per_set=self.games_per_set,
            )
            return rx.redirect(
                f"/league-dashboard?id={league.active_competition_id}"
                if league.active_competition_id
                else "/league-dashboard"
            )

        # Torneo eliminatorio (cuadro con BYEs si nº jugadores no es potencia de 2)
        league.setup_tournament(
            name=name,
            players=clean_players,
            sets_per_match=self.sets_per_match,
            games_per_set=self.games_per_set,
        )
        return rx.redirect(
            f"/tournament-dashboard?id={league.active_competition_id}"
        )
