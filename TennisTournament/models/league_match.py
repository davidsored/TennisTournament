"""LeagueMatch (rx.Model, table=True) — entrada del calendario.

Cada partido pertenece a UNA competición (liga vía `league_id` o torneo vía
`tournament_id`). Los campos específicos de torneo (`bracket_position`,
`next_match_id`, `is_placeholder`) quedan en NULL para partidos de liga.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import reflex as rx
import sqlmodel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LeagueMatch(rx.Model, table=True):
    """Partido del calendario de liga o cuadro eliminatorio."""

    __tablename__ = "league_matches"

    # Asociación a una competición (uno de los dos, nunca ambos).
    league_id: Optional[int] = sqlmodel.Field(
        default=None, foreign_key="leagues.id", index=True
    )
    tournament_id: Optional[int] = sqlmodel.Field(
        default=None, foreign_key="tournaments.id", index=True
    )

    round_num: int = 0
    leg: int = 1  # 1 = ida, 2 = vuelta (sólo aplica a liga)
    home: str = ""
    away: str = ""
    status: str = "Pendiente"
    sets_home: int = 0
    sets_away: int = 0

    # Tournament-specific
    bracket_position: Optional[int] = None
    next_match_id: Optional[int] = None
    is_placeholder: bool = False

    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)
