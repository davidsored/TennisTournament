"""Estado del Tournament Dashboard.

Construye la vista del cuadro a partir de `LeagueState.competitions` filtrando
por `competition_type == "tournament"` y agrupando los partidos en columnas
por `round_num`. Toda la información necesaria para pintar las tarjetas y los
conectores se calcula aquí (banderas booleanas, etiquetas, scores como string).
"""

from __future__ import annotations

import reflex as rx
from pydantic import BaseModel, Field

from .league_state import LeagueState, STATUS_FINALIZADO, STATUS_PENDIENTE


_PLACEHOLDER_PREFIX = "Ganador Partido"


class BracketMatch(BaseModel):
    """Datos planos de un partido para renderizar la card del bracket."""

    id: str = ""
    home: str = ""
    away: str = ""
    home_score: str = "0"
    away_score: str = "0"
    home_winner: bool = False
    away_winner: bool = False
    home_is_placeholder: bool = False
    away_is_placeholder: bool = False
    is_pending: bool = False
    is_finished: bool = False
    is_final: bool = False
    has_pair: bool = False              # ambos slots con jugadores reales
    is_top_half: bool = False           # bracket_position par → conector vertical hacia abajo
    is_bottom_half: bool = False        # bracket_position impar → conector vertical hacia arriba
    has_outgoing: bool = False          # tiene next_match_id (no es la final)
    has_incoming: bool = False          # round_num > 1 (recibe conector de la izquierda)


class BracketColumn(BaseModel):
    """Una columna del cuadro = todos los partidos de una ronda."""

    label: str = ""
    round_num: int = 0
    is_final_column: bool = False
    matches: list[BracketMatch] = Field(default_factory=list)


def _round_label(remaining: int) -> str:
    if remaining == 0:
        return "Final"
    if remaining == 1:
        return "Semifinales"
    if remaining == 2:
        return "Cuartos"
    if remaining == 3:
        return "Octavos"
    if remaining == 4:
        return "Dieciseisavos"
    return f"Ronda {remaining}"


class TournamentState(rx.State):
    """Vista del Tournament Dashboard."""

    # ID del torneo mostrado (0 = ninguno). Lo consume el diálogo de
    # edición de participantes para saber sobre qué competición operar.
    tournament_id: int = 0

    tournament_name: str = ""
    tournament_subtitle: str = ""
    has_tournament: bool = False
    bracket_columns: list[BracketColumn] = []

    async def setup_view(self):
        """Hidrata desde Postgres y arma la vista del torneo via `?id=N`."""
        league = await self.get_state(LeagueState)
        league._hydrate()
        self._build_view(league)

    def _build_view(self, league: LeagueState) -> None:
        """Arma la vista del cuadro desde un `LeagueState` YA hidratado.

        Separado de `setup_view` para que flujos que acaban de mutar y
        re-hidratar (p.ej. renombrar participante) refresquen el bracket
        sin pagar una segunda hidratación completa de la BD.
        """
        # Reset
        self.tournament_id = 0
        self.tournament_name = ""
        self.tournament_subtitle = ""
        self.has_tournament = False
        self.bracket_columns = []

        tournament_id_param = self.router.page.params.get("id", "")
        try:
            tournament_id = int(tournament_id_param) if tournament_id_param else 0
        except (TypeError, ValueError):
            return
        if tournament_id <= 0:
            return

        comp = next(
            (
                c
                for c in league.competitions
                if c.id == tournament_id and c.competition_type == "tournament"
            ),
            None,
        )
        if not comp:
            return

        self.has_tournament = True
        self.tournament_id = comp.id
        self.tournament_name = comp.name
        n_players = len([p for p in comp.players if p.strip()])
        self.tournament_subtitle = f"Cuadro principal · {n_players} jugadores"

        # Agrupar por ronda y ordenar por bracket_position.
        by_round: dict[int, list] = {}
        for m in comp.matches:
            by_round.setdefault(m.round_num, []).append(m)

        if not by_round:
            return

        max_round = max(by_round.keys())
        columns: list[BracketColumn] = []

        for r in sorted(by_round.keys()):
            matches_raw = sorted(
                by_round[r], key=lambda m: (m.bracket_position or 0)
            )
            is_final_col = r == max_round
            remaining = max_round - r
            label = _round_label(remaining)

            bm_list: list[BracketMatch] = []
            for m in matches_raw:
                home_is_placeholder = (
                    not m.home
                    or m.home == "BYE"
                    or m.home.startswith(_PLACEHOLDER_PREFIX)
                )
                away_is_placeholder = (
                    not m.away
                    or m.away == "BYE"
                    or m.away.startswith(_PLACEHOLDER_PREFIX)
                )

                home_winner = (
                    m.status == STATUS_FINALIZADO and m.sets_home > m.sets_away
                )
                away_winner = (
                    m.status == STATUS_FINALIZADO and m.sets_away > m.sets_home
                )

                bracket_pos = (
                    m.bracket_position if m.bracket_position is not None else 0
                )

                bm_list.append(
                    BracketMatch(
                        id=str(m.id),
                        home=(m.home if m.home else "TBD"),
                        away=(m.away if m.away else "TBD"),
                        home_score=str(m.sets_home),
                        away_score=str(m.sets_away),
                        home_winner=home_winner,
                        away_winner=away_winner,
                        home_is_placeholder=home_is_placeholder,
                        away_is_placeholder=away_is_placeholder,
                        is_pending=(m.status == STATUS_PENDIENTE),
                        is_finished=(m.status == STATUS_FINALIZADO),
                        is_final=is_final_col,
                        has_pair=(
                            not home_is_placeholder
                            and not away_is_placeholder
                        ),
                        is_top_half=(bracket_pos % 2 == 0),
                        is_bottom_half=(bracket_pos % 2 == 1),
                        has_outgoing=(not is_final_col),
                        has_incoming=(r > 1),
                    )
                )

            columns.append(
                BracketColumn(
                    label=label,
                    round_num=r,
                    is_final_column=is_final_col,
                    matches=bm_list,
                )
            )

        self.bracket_columns = columns

    @rx.var
    def bracket_min_height(self) -> str:
        """Altura mínima del cuadro: ~150px por cada match de Ronda 1.

        Esto garantiza que `flex-1` en cada wrapper de match dé espacio
        suficiente para la card aunque haya muchos matches en Ronda 1
        (16, 32 jugadores). El alto se propaga vía `align-items: stretch`
        a las columnas de rondas avanzadas, que reparten ese espacio entre
        sus pocos matches → cada uno queda centrado respecto a sus padres.
        """
        if not self.bracket_columns:
            return "500px"
        n_first = max(1, len(self.bracket_columns[0].matches))
        return f"{max(500, n_first * 150)}px"
