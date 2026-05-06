"""Agrupación de fixtures por ronda con pares ida/vuelta alineados.

Función pura usada por `LeagueState.grouped_fixtures` (Round Robin x2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


STATUS_FINALIZADO = "Finalizado"


@dataclass
class FixtureMatch:
    """Entrada de partido para alimentar `group_fixtures`."""

    id: int
    round_num: int
    leg: int  # 1=ida, 2=vuelta
    home: str
    away: str
    status: str
    sets_home: int
    sets_away: int


@dataclass
class FixtureLeg:
    """Datos de UNA pierna (ida o vuelta) ya enriquecidos con flags de ganador."""

    match_id: int
    home: str
    away: str
    status: str
    sets_home: int
    sets_away: int
    home_winner: bool
    away_winner: bool


@dataclass
class FixturePairView:
    """Par (ida, vuelta) alineado por posición."""

    ida: Optional[FixtureLeg] = None
    vuelta: Optional[FixtureLeg] = None


@dataclass
class RoundFixtures:
    round_num: int
    label: str
    pairs: list[FixturePairView] = field(default_factory=list)


def _to_leg(m: FixtureMatch) -> FixtureLeg:
    finished = m.status == STATUS_FINALIZADO
    return FixtureLeg(
        match_id=m.id,
        home=m.home,
        away=m.away,
        status=m.status,
        sets_home=m.sets_home,
        sets_away=m.sets_away,
        home_winner=finished and m.sets_home > m.sets_away,
        away_winner=finished and m.sets_away > m.sets_home,
    )


def group_fixtures(matches: list[FixtureMatch]) -> list[RoundFixtures]:
    """Agrupa los matches por ronda y empareja ida[i] con vuelta[i].

    El orden de inserción dentro de cada ronda determina el emparejamiento:
    el i-ésimo de la ida se alinea con el i-ésimo de la vuelta (que es el
    mismo enfrentamiento con local/visitante intercambiados).
    """
    by_round: dict[int, dict[str, list[FixtureMatch]]] = {}
    for m in matches:
        entry = by_round.setdefault(m.round_num, {"ida": [], "vuelta": []})
        bucket = "ida" if m.leg == 1 else "vuelta"
        entry[bucket].append(m)

    rounds: list[RoundFixtures] = []
    for r in sorted(by_round.keys()):
        ida_list = by_round[r]["ida"]
        vuelta_list = by_round[r]["vuelta"]
        pairs: list[FixturePairView] = []
        for i in range(max(len(ida_list), len(vuelta_list))):
            pair = FixturePairView()
            if i < len(ida_list):
                pair.ida = _to_leg(ida_list[i])
            if i < len(vuelta_list):
                pair.vuelta = _to_leg(vuelta_list[i])
            pairs.append(pair)
        rounds.append(RoundFixtures(round_num=r, label=f"Ronda {r}", pairs=pairs))

    return rounds
