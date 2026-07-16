"""Estado del diálogo de edición de participantes.

State fino de UI (patrón HomeState→LeagueState): gestiona el diálogo, la
fila en edición y los mensajes de error; delega la mutación transaccional
en `LeagueState.rename_player`. Sirve tanto para ligas (league_dashboard)
como para torneos (tournament_dashboard).
"""

from __future__ import annotations

import reflex as rx

from .league_state import LeagueState
from .tournament_state import TournamentState


class PlayerEditState(rx.State):
    """Diálogo "Editar participantes" de los dashboards."""

    dialog_open: bool = False

    # Competición sobre la que opera el diálogo.
    comp_id: int = 0
    comp_type: str = ""  # "league" | "tournament"

    # Snapshot de los participantes para renderizar la lista.
    players: list[str] = []

    # Fila en edición ("" = ninguna) y su input asociado.
    editing_name: str = ""
    input_value: str = ""
    error_message: str = ""

    # ---------------- Helpers ----------------

    def _refresh_players(self, league: LeagueState) -> None:
        comp = next(
            (
                c
                for c in league.competitions
                if c.id == self.comp_id
                and c.competition_type == self.comp_type
            ),
            None,
        )
        self.players = list(comp.players) if comp else []

    def _reset_edit_row(self) -> None:
        self.editing_name = ""
        self.input_value = ""
        self.error_message = ""

    # ---------------- Event handlers ----------------

    async def open_dialog(self, comp_id: int, comp_type: str):
        """Abre el diálogo con los participantes de la competición dada."""
        self.comp_id = comp_id
        self.comp_type = comp_type
        self._reset_edit_row()
        league = await self.get_state(LeagueState)
        self._refresh_players(league)
        self.dialog_open = True

    def set_dialog_open(self, value: bool) -> None:
        self.dialog_open = value
        if not value:
            self._reset_edit_row()

    def start_edit(self, name: str) -> None:
        self.editing_name = name
        self.input_value = name
        self.error_message = ""

    def cancel_edit(self) -> None:
        self._reset_edit_row()

    def set_input_value(self, value: str) -> None:
        self.input_value = value
        self.error_message = ""

    async def save_edit(self):
        """Guarda el renombrado delegando en `LeagueState.rename_player`."""
        league = await self.get_state(LeagueState)
        error = league.rename_player(
            self.comp_id, self.comp_type, self.editing_name, self.input_value
        )
        if error:
            self.error_message = error
            return

        self._refresh_players(league)
        self._reset_edit_row()

        # El bracket de torneo se construye en TournamentState: re-armarlo
        # para que la vista refleje el nombre nuevo sin recargar la página.
        # `rename_player` ya re-hidrató LeagueState, así que basta reconstruir.
        if self.comp_type == "tournament":
            tournament = await self.get_state(TournamentState)
            tournament._build_view(league)

        return rx.toast.success("Participante renombrado")
