"""Estado de la liga (Round Robin x2) — soporta múltiples competiciones simultáneas."""

from __future__ import annotations

import random
from typing import Optional
from uuid import uuid4

import reflex as rx
from pydantic import BaseModel, Field

from ..models.league import round_robin


STATUS_PENDIENTE = "Pendiente"
STATUS_EN_CURSO = "En curso"
STATUS_FINALIZADO = "Finalizado"


class LeagueMatch(BaseModel):
    """Partido del calendario de liga."""

    id: int = 0
    round_num: int = 0
    leg: int = 1  # 1 = ida, 2 = vuelta
    home: str = ""
    away: str = ""
    status: str = STATUS_PENDIENTE
    sets_home: int = 0
    sets_away: int = 0


class Competition(BaseModel):
    """Una competición independiente (liga o torneo) con su propio calendario."""

    id: str = ""
    name: str = ""
    competition_type: str = "league"
    players: list[str] = Field(default_factory=list)
    matches: list[LeagueMatch] = Field(default_factory=list)
    sets_per_match: int = 3
    games_per_set: int = 6


class FixturePair(BaseModel):
    """Par ida/vuelta de la misma ronda alineados (B vs A para vuelta)."""

    has_ida: bool = False
    ida_id: str = ""
    ida_home: str = ""
    ida_away: str = ""
    ida_status: str = STATUS_PENDIENTE
    ida_sets_home: str = "0"
    ida_sets_away: str = "0"
    ida_home_winner: bool = False
    ida_away_winner: bool = False

    has_vuelta: bool = False
    vuelta_id: str = ""
    vuelta_home: str = ""
    vuelta_away: str = ""
    vuelta_status: str = STATUS_PENDIENTE
    vuelta_sets_home: str = "0"
    vuelta_sets_away: str = "0"
    vuelta_home_winner: bool = False
    vuelta_away_winner: bool = False


class RoundView(BaseModel):
    """Una ronda con su etiqueta y los pares de partidos (ida/vuelta)."""

    round_num: int = 0
    label: str = ""
    pairs: list[FixturePair] = Field(default_factory=list)


class LeagueState(rx.State):
    """Estado global de competiciones.

    `competitions` es la fuente de verdad: cada nueva liga/torneo se añade sin
    borrar las anteriores. `active_id` indica cuál se muestra actualmente en el
    dashboard. Los campos planos (`league_name`, `players`, `matches`, …) son
    computed vars que apuntan a la competición activa para que el resto del
    código (dashboard, scoreboard, etc.) siga funcionando sin cambios.
    """

    competitions: list[Competition] = []
    active_id: str = ""

    # ---------------- Lifecycle ----------------

    def setup_dashboard(self) -> None:
        """Selecciona la competición a mostrar leyendo `?id=…` de la URL."""
        comp_id = self.router.page.params.get("id", "")
        if comp_id and any(c.id == comp_id for c in self.competitions):
            self.active_id = comp_id
            return
        # Fallback: si la activa ya no existe, queda la última creada.
        if self.competitions and not any(
            c.id == self.active_id for c in self.competitions
        ):
            self.active_id = self.competitions[-1].id

    def setup_league(
        self,
        name: str,
        players: list[str],
        sets_per_match: int = 3,
        games_per_set: int = 6,
    ) -> None:
        """Crea una NUEVA liga (no sobreescribe). Genera calendario aleatorio."""
        clean = [p.strip() for p in players if p.strip()]
        if not clean:
            return

        seeding = list(clean)
        random.shuffle(seeding)

        # IDs únicos globalmente (entre todas las competiciones).
        next_id = (
            max(
                (m.id for c in self.competitions for m in c.matches),
                default=0,
            )
            + 1
        )
        matches = self._build_calendar(seeding, starting_id=next_id)

        new_comp = Competition(
            id=str(uuid4()),
            name=name or "Liga sin nombre",
            competition_type="league",
            players=clean,
            matches=matches,
            sets_per_match=sets_per_match,
            games_per_set=games_per_set,
        )
        # Crucial: append, no reasignación destructiva.
        self.competitions = self.competitions + [new_comp]
        self.active_id = new_comp.id

    @staticmethod
    def _build_calendar(players: list[str], starting_id: int = 1) -> list[LeagueMatch]:
        """Ida y vuelta con `round_num` compartido. IDs empiezan en `starting_id`."""
        base_rounds = round_robin(players)
        out: list[LeagueMatch] = []
        idx = starting_id - 1
        for r, round_matches in enumerate(base_rounds, start=1):
            for home, away in round_matches:
                idx += 1
                out.append(
                    LeagueMatch(
                        id=idx, round_num=r, leg=1,
                        home=home, away=away, status=STATUS_PENDIENTE,
                    )
                )
            for home, away in round_matches:
                idx += 1
                out.append(
                    LeagueMatch(
                        id=idx, round_num=r, leg=2,
                        home=away, away=home, status=STATUS_PENDIENTE,
                    )
                )
        return out

    # ---------------- Mutadores ----------------

    def record_result(
        self, match_id: int, sets_home: int, sets_away: int
    ) -> None:
        """Cierra un partido en la competición que lo contenga."""
        for comp in self.competitions:
            for m in comp.matches:
                if m.id == match_id:
                    m.sets_home = sets_home
                    m.sets_away = sets_away
                    m.status = STATUS_FINALIZADO
                    # Actualiza la activa para que `/league-dashboard` muestre
                    # la liga del partido recién cerrado.
                    self.active_id = comp.id
                    # Reasignación para forzar reactividad de Reflex.
                    self.competitions = list(self.competitions)
                    return

    # ---------------- Helpers internos ----------------

    def _active(self) -> Optional[Competition]:
        if not self.active_id:
            return None
        return next(
            (c for c in self.competitions if c.id == self.active_id), None
        )

    # ---------------- Computed: vista de la competición activa ----------------

    @rx.var
    def league_name(self) -> str:
        c = self._active()
        return c.name if c else ""

    @rx.var
    def players(self) -> list[str]:
        c = self._active()
        return list(c.players) if c else []

    @rx.var
    def matches(self) -> list[LeagueMatch]:
        c = self._active()
        return list(c.matches) if c else []

    @rx.var
    def sets_per_match(self) -> int:
        c = self._active()
        return c.sets_per_match if c else 3

    @rx.var
    def games_per_set(self) -> int:
        c = self._active()
        return c.games_per_set if c else 6

    @rx.var
    def has_league(self) -> bool:
        c = self._active()
        return c is not None and len(c.matches) > 0

    @rx.var
    def total_rounds(self) -> int:
        c = self._active()
        if not c or not c.matches:
            return 0
        return max((m.round_num for m in c.matches), default=0)

    # ---------------- Computed: clasificación ----------------

    @rx.var
    def standings(self) -> list[dict[str, str]]:
        c = self._active()
        if not c or not c.players:
            return []

        table: dict[str, dict[str, int]] = {
            p: {"pj": 0, "pg": 0, "pp": 0, "sw": 0, "sl": 0, "pts": 0}
            for p in c.players
        }

        for m in c.matches:
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
            {
                "pos": str(i + 1),
                "player": name,
                "pj": str(s["pj"]),
                "pg": str(s["pg"]),
                "pp": str(s["pp"]),
                "sets": f"{s['sw']}-{s['sl']}",
                "pts": str(s["pts"]),
            }
            for i, (name, s) in enumerate(rows)
        ]

    # ---------------- Computed: fixtures agrupados ----------------

    @rx.var
    def grouped_fixtures(self) -> list[RoundView]:
        c = self._active()
        if not c:
            return []

        by_round: dict[int, dict[str, list[LeagueMatch]]] = {}
        for m in c.matches:
            entry = by_round.setdefault(m.round_num, {"ida": [], "vuelta": []})
            (entry["ida"] if m.leg == 1 else entry["vuelta"]).append(m)

        rounds: list[RoundView] = []
        for r in sorted(by_round.keys()):
            ida_list = by_round[r]["ida"]
            vuelta_list = by_round[r]["vuelta"]
            pairs: list[FixturePair] = []
            for i in range(max(len(ida_list), len(vuelta_list))):
                ida = ida_list[i] if i < len(ida_list) else None
                vuelta = vuelta_list[i] if i < len(vuelta_list) else None
                pair = FixturePair()

                if ida is not None:
                    pair.has_ida = True
                    pair.ida_id = str(ida.id)
                    pair.ida_home = ida.home
                    pair.ida_away = ida.away
                    pair.ida_status = ida.status
                    pair.ida_sets_home = str(ida.sets_home)
                    pair.ida_sets_away = str(ida.sets_away)
                    finished = ida.status == STATUS_FINALIZADO
                    pair.ida_home_winner = finished and ida.sets_home > ida.sets_away
                    pair.ida_away_winner = finished and ida.sets_away > ida.sets_home

                if vuelta is not None:
                    pair.has_vuelta = True
                    pair.vuelta_id = str(vuelta.id)
                    pair.vuelta_home = vuelta.home
                    pair.vuelta_away = vuelta.away
                    pair.vuelta_status = vuelta.status
                    pair.vuelta_sets_home = str(vuelta.sets_home)
                    pair.vuelta_sets_away = str(vuelta.sets_away)
                    finished = vuelta.status == STATUS_FINALIZADO
                    pair.vuelta_home_winner = (
                        finished and vuelta.sets_home > vuelta.sets_away
                    )
                    pair.vuelta_away_winner = (
                        finished and vuelta.sets_away > vuelta.sets_home
                    )

                pairs.append(pair)

            rounds.append(RoundView(round_num=r, label=f"Ronda {r}", pairs=pairs))

        return rounds
