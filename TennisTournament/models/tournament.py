"""Tournament model (rx.Model, table=True) — bracket eliminatorio."""

from __future__ import annotations

from datetime import datetime, timezone

import reflex as rx
import sqlmodel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tournament(rx.Model, table=True):
    """Torneo eliminatorio persistido en Postgres."""

    __tablename__ = "tournaments"

    name: str
    sets_per_match: int = 3
    games_per_set: int = 6
    players_json: str = "[]"  # JSON list of player names
    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)
