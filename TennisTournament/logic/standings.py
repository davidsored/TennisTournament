"""Cálculo puro de la tabla de clasificación de una liga.

Independiente de Reflex / SQLModel — recibe `MatchResult` (dataclass simple)
y devuelve `StandingsRow`. Reglas implementadas:
  - 3 puntos por victoria, 0 por derrota.
  - 1 + 1 en empates por robustez (no debería ocurrir en tenis).
  - Desempate: puntos → diferencia de sets (sw - sl) → orden alfabético.
"""

from __future__ import annotations

from dataclasses import dataclass


STATUS_FINALIZADO = "Finalizado"


@dataclass
class MatchResult:
    """Partido finalizado de una liga (sin BYEs)."""

    home: str
    away: str
    sets_home: int
    sets_away: int
    status: str = STATUS_FINALIZADO


@dataclass
class StandingsRow:
    pos: int
    player: str
    pj: int
    pg: int
    pp: int
    sets_won: int
    sets_lost: int
    pts: int


def compute_standings(
    players: list[str], matches: list[MatchResult]
) -> list[StandingsRow]:
    """Calcula la tabla a partir de los partidos finalizados."""
    if not players:
        return []

    table: dict[str, dict[str, int]] = {
        p: {"pj": 0, "pg": 0, "pp": 0, "sw": 0, "sl": 0, "pts": 0}
        for p in players
    }

    for m in matches:
        if m.status != STATUS_FINALIZADO:
            continue
        if m.home not in table or m.away not in table:
            continue

        table[m.home]["pj"] += 1
        table[m.away]["pj"] += 1

        if m.sets_home == m.sets_away:
            table[m.home]["pts"] += 1
            table[m.away]["pts"] += 1
            continue

        if m.sets_home > m.sets_away:
            winner, loser = m.home, m.away
            w_sets, l_sets = m.sets_home, m.sets_away
        else:
            winner, loser = m.away, m.home
            w_sets, l_sets = m.sets_away, m.sets_home

        table[winner]["pg"] += 1
        table[winner]["pts"] += 3
        table[loser]["pp"] += 1
        table[winner]["sw"] += w_sets
        table[winner]["sl"] += l_sets
        table[loser]["sw"] += l_sets
        table[loser]["sl"] += w_sets

    rows = sorted(
        table.items(),
        key=lambda kv: (-kv[1]["pts"], -(kv[1]["sw"] - kv[1]["sl"]), kv[0]),
    )

    return [
        StandingsRow(
            pos=i + 1,
            player=name,
            pj=s["pj"],
            pg=s["pg"],
            pp=s["pp"],
            sets_won=s["sw"],
            sets_lost=s["sl"],
            pts=s["pts"],
        )
        for i, (name, s) in enumerate(rows)
    ]
