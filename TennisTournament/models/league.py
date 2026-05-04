"""League model (rx.Model, table=True) + algoritmo Round Robin (ida y vuelta).

Persistido en Supabase como tabla `leagues`. La lista de jugadores se almacena
serializada en JSON en `players_json` para evitar una tabla extra.
"""

from __future__ import annotations

from datetime import datetime, timezone

import reflex as rx
import sqlmodel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class League(rx.Model, table=True):
    """Liga (Round Robin) persistida en Postgres."""

    __tablename__ = "leagues"

    name: str
    sets_per_match: int = 3
    games_per_set: int = 6
    players_json: str = "[]"  # JSON list of player names
    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)


# --------------------------- Round Robin ---------------------------

_BYE = "__BYE__"


def round_robin(players: list[str]) -> list[list[tuple[str, str]]]:
    """Genera el calendario Round Robin (sólo ida) usando algoritmo del círculo."""
    if len(players) < 2:
        return []

    pool = list(players)
    if len(pool) % 2 == 1:
        pool.append(_BYE)

    n = len(pool)
    half = n // 2
    rotation = list(pool)
    rounds: list[list[tuple[str, str]]] = []

    for _ in range(n - 1):
        round_matches: list[tuple[str, str]] = []
        for i in range(half):
            home = rotation[i]
            away = rotation[n - 1 - i]
            if home != _BYE and away != _BYE:
                round_matches.append((home, away))
        rounds.append(round_matches)
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

    return rounds


def round_robin_double(players: list[str]) -> list[list[tuple[str, str, int]]]:
    """Round Robin doble vuelta (ida + vuelta intercambiando local/visitante)."""
    base = round_robin(players)
    out: list[list[tuple[str, str, int]]] = []
    for rnd in base:
        out.append([(h, a, 1) for h, a in rnd])
    for rnd in base:
        out.append([(a, h, 2) for h, a in rnd])
    return out
