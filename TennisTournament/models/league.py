"""League model + algoritmo Round Robin (ida y vuelta)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .match import Match
from .player import Player


@dataclass
class League:
    """Modelo de liga (estructura base — la persistencia vive en LeagueState)."""

    name: str
    players: list[Player] = field(default_factory=list)
    matches: list[Match] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))


# --------------------------- Round Robin ---------------------------

_BYE = "__BYE__"


def round_robin(players: list[str]) -> list[list[tuple[str, str]]]:
    """Genera el calendario Round Robin (sólo ida).

    Devuelve una lista de rondas; cada ronda es una lista de pares
    `(local, visitante)`. Si el número de jugadores es impar, añade un "BYE"
    (descanso) que se omite en la salida final.

    Algoritmo del círculo: fija el primer jugador y rota el resto.
    Para `n` jugadores genera `n - 1` rondas con `n // 2` partidos por ronda.
    """
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
        # Rota: fija el primero, mueve el último al puesto 1.
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

    return rounds


def round_robin_double(players: list[str]) -> list[list[tuple[str, str, int]]]:
    """Round Robin a doble vuelta.

    Devuelve rondas; cada elemento es `(local, visitante, leg)` donde
    `leg=1` es ida y `leg=2` es vuelta (con local/visitante intercambiados).
    """
    base = round_robin(players)
    out: list[list[tuple[str, str, int]]] = []
    for rnd in base:
        out.append([(h, a, 1) for h, a in rnd])
    for rnd in base:
        out.append([(a, h, 2) for h, a in rnd])
    return out
