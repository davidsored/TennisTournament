"""Estado de competiciones — backed por Supabase vía rx.session().

Las mutaciones (crear liga/torneo, registrar resultado, eliminar) escriben a
PostgreSQL con add+commit. La hidratación (`_hydrate`) lee leagues, tournaments
y league_matches y construye las vistas pydantic transitorias que consumen los
componentes UI (CompetitionView / FixturePair / RoundView).
"""

from __future__ import annotations

import json
import math
import random
from typing import Optional

import reflex as rx
from pydantic import BaseModel, Field
from sqlmodel import select

from ..models.league import League, round_robin
from ..models.league_match import LeagueMatch
from ..models.tournament import Tournament


STATUS_PENDIENTE = "Pendiente"
STATUS_EN_CURSO = "En curso"
STATUS_FINALIZADO = "Finalizado"


# ----- Pydantic transient views (no persistidos) -----


class FixturePair(BaseModel):
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
    round_num: int = 0
    label: str = ""
    pairs: list[FixturePair] = Field(default_factory=list)


class MatchView(BaseModel):
    """Vista plana de LeagueMatch para consumo desde Reflex."""

    id: int = 0
    league_id: Optional[int] = None
    tournament_id: Optional[int] = None
    round_num: int = 0
    leg: int = 1
    home: str = ""
    away: str = ""
    status: str = STATUS_PENDIENTE
    sets_home: int = 0
    sets_away: int = 0
    bracket_position: Optional[int] = None
    next_match_id: Optional[int] = None
    is_placeholder: bool = False


class CompetitionView(BaseModel):
    """Snapshot de una competición (League o Tournament) con sus matches."""

    id: int = 0
    name: str = ""
    competition_type: str = "league"
    players: list[str] = Field(default_factory=list)
    sets_per_match: int = 3
    games_per_set: int = 6
    matches: list[MatchView] = Field(default_factory=list)


def _league_match_to_view(m: LeagueMatch) -> MatchView:
    return MatchView(
        id=m.id or 0,
        league_id=m.league_id,
        tournament_id=m.tournament_id,
        round_num=m.round_num,
        leg=m.leg,
        home=m.home,
        away=m.away,
        status=m.status,
        sets_home=m.sets_home,
        sets_away=m.sets_away,
        bracket_position=m.bracket_position,
        next_match_id=m.next_match_id,
        is_placeholder=m.is_placeholder,
    )


def _safe_players(json_str: str) -> list[str]:
    try:
        data = json.loads(json_str) if json_str else []
        return [str(p) for p in data if isinstance(p, str)]
    except (json.JSONDecodeError, TypeError):
        return []


class LeagueState(rx.State):
    """Estado global de competiciones (persistido en Supabase)."""

    # Snapshot cargado desde la DB (la única fuente de verdad real).
    competitions: list[CompetitionView] = []

    # Competición activa para el dashboard (id de DB + tipo).
    active_competition_id: int = 0
    active_competition_type: str = ""  # "league" o "tournament"

    # ---------------- Hydration ----------------

    def _hydrate(self) -> None:
        """Recarga la lista de competiciones desde la base de datos."""
        with rx.session() as session:
            leagues = session.exec(select(League)).all()
            tournaments = session.exec(select(Tournament)).all()
            all_matches = session.exec(select(LeagueMatch)).all()

        comps: list[CompetitionView] = []

        for lg in leagues:
            league_matches = [
                _league_match_to_view(m) for m in all_matches if m.league_id == lg.id
            ]
            comps.append(
                CompetitionView(
                    id=lg.id or 0,
                    name=lg.name,
                    competition_type="league",
                    players=_safe_players(lg.players_json),
                    sets_per_match=lg.sets_per_match,
                    games_per_set=lg.games_per_set,
                    matches=league_matches,
                )
            )

        for tr in tournaments:
            tournament_matches = [
                _league_match_to_view(m)
                for m in all_matches
                if m.tournament_id == tr.id
            ]
            comps.append(
                CompetitionView(
                    id=tr.id or 0,
                    name=tr.name,
                    competition_type="tournament",
                    players=_safe_players(tr.players_json),
                    sets_per_match=tr.sets_per_match,
                    games_per_set=tr.games_per_set,
                    matches=tournament_matches,
                )
            )

        self.competitions = comps

    # ---------------- Lifecycle ----------------

    def setup_dashboard(self) -> None:
        """Hidrata y selecciona la liga activa según `?id=N` (DB id)."""
        self._hydrate()

        comp_id_param = self.router.page.params.get("id", "")
        try:
            target_id = int(comp_id_param) if comp_id_param else 0
        except (TypeError, ValueError):
            target_id = 0

        # Busca específicamente liga (el dashboard de liga sólo muestra ligas).
        target = next(
            (
                c
                for c in self.competitions
                if c.id == target_id and c.competition_type == "league"
            ),
            None,
        )
        if target is None:
            leagues = [
                c for c in self.competitions if c.competition_type == "league"
            ]
            target = leagues[-1] if leagues else None

        if target:
            self.active_competition_id = target.id
            self.active_competition_type = target.competition_type
        else:
            self.active_competition_id = 0
            self.active_competition_type = ""

    # ---------------- Mutators (rx.session add + commit) ----------------

    def setup_league(
        self,
        name: str,
        players: list[str],
        sets_per_match: int = 3,
        games_per_set: int = 6,
    ) -> None:
        """Crea una NUEVA liga en Postgres + calendario Round Robin x2."""
        if not name or not name.strip():
            return
        clean = [p.strip() for p in players if p.strip()]
        if len(clean) < 2:
            return

        seeding = list(clean)
        random.shuffle(seeding)
        rounds = round_robin(seeding)

        with rx.session() as session:
            league = League(
                name=name.strip(),
                sets_per_match=sets_per_match,
                games_per_set=games_per_set,
                players_json=json.dumps(clean),
            )
            session.add(league)
            session.commit()
            session.refresh(league)

            for r, round_matches in enumerate(rounds, start=1):
                for home, away in round_matches:
                    session.add(
                        LeagueMatch(
                            league_id=league.id,
                            round_num=r,
                            leg=1,
                            home=home,
                            away=away,
                            status=STATUS_PENDIENTE,
                        )
                    )
                for home, away in round_matches:
                    session.add(
                        LeagueMatch(
                            league_id=league.id,
                            round_num=r,
                            leg=2,
                            home=away,
                            away=home,
                            status=STATUS_PENDIENTE,
                        )
                    )
            session.commit()

            self.active_competition_id = league.id or 0
            self.active_competition_type = "league"

        self._hydrate()

    def setup_tournament(
        self,
        name: str,
        players: list[str],
        sets_per_match: int = 3,
        games_per_set: int = 6,
    ) -> None:
        """Crea un NUEVO torneo eliminatorio en Postgres con bracket completo."""
        if not name or not name.strip():
            return
        real = [p.strip() for p in players if p.strip()]
        if len(real) < 2:
            return

        random.shuffle(real)
        n_players = len(real)
        bracket_size = 1
        while bracket_size < n_players:
            bracket_size *= 2
        n_byes = bracket_size - n_players

        # Distribuir BYEs: cada uno emparejado con un real.
        seeding: list[str] = []
        for i in range(n_byes):
            seeding.append(real[i])
            seeding.append("BYE")
        for i in range(n_byes, n_players):
            seeding.append(real[i])

        total_rounds = int(math.log2(bracket_size))
        winner_set_count = sets_per_match // 2 + 1

        with rx.session() as session:
            tournament = Tournament(
                name=name.strip(),
                sets_per_match=sets_per_match,
                games_per_set=games_per_set,
                players_json=json.dumps(real),
            )
            session.add(tournament)
            session.commit()
            session.refresh(tournament)

            # Fase 1: crear todos los partidos sin next_match_id (DB asigna ids).
            rounds_matches: list[list[LeagueMatch]] = []
            for r in range(total_rounds):
                n_in_round = bracket_size // (2 ** (r + 1))
                this_round: list[LeagueMatch] = []
                for p in range(n_in_round):
                    m = LeagueMatch(
                        tournament_id=tournament.id,
                        round_num=r + 1,
                        leg=1,
                        home="",
                        away="",
                        status=STATUS_PENDIENTE,
                        bracket_position=p,
                        is_placeholder=(r > 0),
                    )
                    session.add(m)
                    this_round.append(m)
                rounds_matches.append(this_round)
            session.commit()
            for rnd in rounds_matches:
                for m in rnd:
                    session.refresh(m)

            # Fase 2: cablear next_match_id (ya con ids reales de Postgres).
            for r in range(total_rounds - 1):
                for p, m in enumerate(rounds_matches[r]):
                    m.next_match_id = rounds_matches[r + 1][p // 2].id

            # Fase 3: poblar Ronda 1 con jugadores y BYEs.
            for p, m in enumerate(rounds_matches[0]):
                m.home = seeding[p * 2]
                m.away = seeding[p * 2 + 1]
                m.is_placeholder = False
                if m.home == "BYE" and m.away != "BYE":
                    m.status = STATUS_FINALIZADO
                    m.sets_home = 0
                    m.sets_away = winner_set_count
                elif m.away == "BYE" and m.home != "BYE":
                    m.status = STATUS_FINALIZADO
                    m.sets_home = winner_set_count
                    m.sets_away = 0

            # Fase 4: propagar BYE winners a Ronda 2.
            all_flat = [m for rnd in rounds_matches for m in rnd]
            for m in rounds_matches[0]:
                if m.status != STATUS_FINALIZADO or m.next_match_id is None:
                    continue
                winner = m.home if m.sets_home > m.sets_away else m.away
                if not winner or winner == "BYE":
                    continue
                target = next(
                    (x for x in all_flat if x.id == m.next_match_id), None
                )
                if target is None or m.bracket_position is None:
                    continue
                if m.bracket_position % 2 == 0:
                    target.home = winner
                else:
                    target.away = winner
                if target.home and target.away:
                    target.is_placeholder = False

            # Fase 5: rellenar slots vacíos con etiquetas "Ganador Partido X".
            for r in range(1, total_rounds):
                for p, m in enumerate(rounds_matches[r]):
                    prev_a = rounds_matches[r - 1][p * 2]
                    prev_b = rounds_matches[r - 1][p * 2 + 1]
                    if not m.home:
                        m.home = f"Ganador Partido {prev_a.id}"
                    if not m.away:
                        m.away = f"Ganador Partido {prev_b.id}"

            # Persistir todos los cambios de Fases 2-5 en una sola transacción.
            session.commit()

            self.active_competition_id = tournament.id or 0
            self.active_competition_type = "tournament"

        self._hydrate()

    def record_result(
        self, match_id: int, sets_home: int, sets_away: int
    ) -> None:
        """Cierra un partido en DB y, si es de torneo, propaga el ganador."""
        with rx.session() as session:
            m = session.get(LeagueMatch, match_id)
            if m is None:
                return

            m.sets_home = sets_home
            m.sets_away = sets_away
            m.status = STATUS_FINALIZADO

            # Lógica de ascenso para torneos.
            if (
                m.tournament_id is not None
                and m.next_match_id is not None
                and m.bracket_position is not None
            ):
                winner = m.home if sets_home > sets_away else m.away
                if winner:
                    nxt = session.get(LeagueMatch, m.next_match_id)
                    if nxt is not None:
                        if m.bracket_position % 2 == 0:
                            nxt.home = winner
                        else:
                            nxt.away = winner
                        if (
                            nxt.home
                            and nxt.away
                            and not nxt.home.startswith("Ganador Partido")
                            and not nxt.away.startswith("Ganador Partido")
                        ):
                            nxt.is_placeholder = False
                        session.add(nxt)

            session.add(m)
            session.commit()

            # Recordamos qué competición tocar para el dashboard.
            if m.league_id is not None:
                self.active_competition_id = m.league_id
                self.active_competition_type = "league"
            elif m.tournament_id is not None:
                self.active_competition_id = m.tournament_id
                self.active_competition_type = "tournament"

        self._hydrate()

    def delete_competition(self, comp_id: int) -> None:
        """Elimina una competición y sus partidos (sólo invocado tras check admin)."""
        try:
            cid = int(comp_id) if not isinstance(comp_id, int) else comp_id
        except (TypeError, ValueError):
            return
        if cid <= 0:
            return

        comp = next((c for c in self.competitions if c.id == cid), None)

        with rx.session() as session:
            if comp is None or comp.competition_type == "league":
                # Borrar partidos de liga
                matches_q = session.exec(
                    select(LeagueMatch).where(LeagueMatch.league_id == cid)
                ).all()
                for m in matches_q:
                    session.delete(m)
                lg = session.get(League, cid)
                if lg is not None:
                    session.delete(lg)
            if comp is None or comp.competition_type == "tournament":
                matches_q = session.exec(
                    select(LeagueMatch).where(LeagueMatch.tournament_id == cid)
                ).all()
                for m in matches_q:
                    session.delete(m)
                tr = session.get(Tournament, cid)
                if tr is not None:
                    session.delete(tr)
            session.commit()

        if self.active_competition_id == cid:
            self.active_competition_id = 0
            self.active_competition_type = ""

        self._hydrate()

    # ---------------- Helpers ----------------

    def _active(self) -> Optional[CompetitionView]:
        if not self.active_competition_id:
            return None
        return next(
            (
                c
                for c in self.competitions
                if c.id == self.active_competition_id
                and c.competition_type == self.active_competition_type
            ),
            None,
        )

    # ---------------- Computed (vista de la competición activa) ----------------

    @rx.var
    def league_name(self) -> str:
        c = self._active()
        return c.name if c else ""

    @rx.var
    def players(self) -> list[str]:
        c = self._active()
        return list(c.players) if c else []

    @rx.var
    def matches(self) -> list[MatchView]:
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

        by_round: dict[int, dict[str, list[MatchView]]] = {}
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
