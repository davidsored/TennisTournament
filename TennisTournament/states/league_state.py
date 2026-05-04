"""Estado de la liga (Round Robin x2) — soporta múltiples competiciones simultáneas."""

from __future__ import annotations

import math
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
    """Partido del calendario.

    Soporta tanto el formato Liga (Round Robin x2) como el formato Torneo
    eliminatorio. Los campos `tournament_id`, `bracket_position`,
    `next_match_id` e `is_placeholder` solo se usan cuando el partido pertenece
    a un torneo eliminatorio (en liga quedan en sus valores por defecto).
    """

    id: int = 0
    round_num: int = 0
    leg: int = 1  # 1 = ida, 2 = vuelta (sólo aplica a liga)
    home: str = ""
    away: str = ""
    status: str = STATUS_PENDIENTE
    sets_home: int = 0
    sets_away: int = 0

    # ---- Campos específicos de torneo eliminatorio ----
    tournament_id: Optional[str] = None        # agrupa partidos del mismo cuadro
    bracket_position: Optional[int] = None     # índice dentro de la ronda
    next_match_id: Optional[int] = None        # id del partido al que avanza el ganador
    is_placeholder: bool = False               # True si los nombres aún no están resueltos


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

    def setup_tournament(
        self,
        name: str,
        players: list[str],
        sets_per_match: int = 3,
        games_per_set: int = 6,
    ) -> None:
        """Crea un NUEVO torneo eliminatorio con cuadro completo.

        Algoritmo:
        1) Sortea aleatoriamente los jugadores reales.
        2) Calcula `bracket_size` como la siguiente potencia de 2 ≥ N de jugadores.
        3) Genera el seeding garantizando que cada BYE se empareje con un jugador
           real (nunca BYE vs BYE).
        4) Crea los partidos por ronda (1 → final), asignando IDs únicos globales.
        5) Cablea `next_match_id` para que cada partido conozca su sucesor.
        6) Coloca a los jugadores reales y BYEs en los partidos de Ronda 1; los
           BYEs auto-finalizan el partido y el jugador real avanza a Ronda 2.
        7) Rellena los slots aún vacíos de las rondas avanzadas con etiquetas
           del tipo `"Ganador Partido X"` (placeholders) hasta que se resuelvan
           las rondas previas.
        """
        # Validación defensiva (la UI ya valida en ConfigState.save_config).
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

        # Distribuir BYEs: cada BYE se empareja con un jugador real para evitar
        # combinaciones BYE vs BYE (sin sentido).
        seeding: list[str] = []
        for i in range(n_byes):
            seeding.append(real[i])
            seeding.append("BYE")
        for i in range(n_byes, n_players):
            seeding.append(real[i])

        total_rounds = int(math.log2(bracket_size))
        tournament_id = str(uuid4())

        next_global_id = (
            max(
                (m.id for c in self.competitions for m in c.matches),
                default=0,
            )
            + 1
        )

        # Construye partidos en cascada (Ronda 1 → Final). El siguiente paso
        # cablea los `next_match_id` una vez se conocen todos los IDs.
        rounds_matches: list[list[LeagueMatch]] = []
        current_id = next_global_id
        for r in range(total_rounds):
            n_in_round = bracket_size // (2 ** (r + 1))
            this_round: list[LeagueMatch] = []
            for p in range(n_in_round):
                this_round.append(
                    LeagueMatch(
                        id=current_id,
                        round_num=r + 1,
                        leg=1,
                        home="",
                        away="",
                        status=STATUS_PENDIENTE,
                        tournament_id=tournament_id,
                        bracket_position=p,
                        next_match_id=None,
                        is_placeholder=(r > 0),
                    )
                )
                current_id += 1
            rounds_matches.append(this_round)

        # Cablea `next_match_id`: posición p en ronda r → posición p // 2 en ronda r+1.
        for r in range(total_rounds - 1):
            for p, m in enumerate(rounds_matches[r]):
                m.next_match_id = rounds_matches[r + 1][p // 2].id

        # Llena Ronda 1 con el seeding. BYE auto-finaliza con derrota total para BYE.
        winner_set_count = sets_per_match // 2 + 1  # sets necesarios para ganar
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

        all_matches = [m for rnd in rounds_matches for m in rnd]

        # Propaga ganadores de BYE de Ronda 1 a Ronda 2.
        for m in rounds_matches[0]:
            if m.status != STATUS_FINALIZADO or m.next_match_id is None:
                continue
            winner = m.home if m.sets_home > m.sets_away else m.away
            if not winner or winner == "BYE":
                continue
            target = next((x for x in all_matches if x.id == m.next_match_id), None)
            if target is None or m.bracket_position is None:
                continue
            if m.bracket_position % 2 == 0:
                target.home = winner
            else:
                target.away = winner
            if target.home and target.away:
                target.is_placeholder = False

        # Rellena slots vacíos de rondas avanzadas con "Ganador Partido X".
        for r in range(1, total_rounds):
            for p, m in enumerate(rounds_matches[r]):
                prev_a = rounds_matches[r - 1][p * 2]
                prev_b = rounds_matches[r - 1][p * 2 + 1]
                if not m.home:
                    m.home = f"Ganador Partido {prev_a.id}"
                if not m.away:
                    m.away = f"Ganador Partido {prev_b.id}"

        new_comp = Competition(
            id=tournament_id,
            name=name or "Torneo sin nombre",
            competition_type="tournament",
            players=real,
            matches=all_matches,
            sets_per_match=sets_per_match,
            games_per_set=games_per_set,
        )
        # Inserción atómica (transacción equivalente sobre la lista en memoria).
        self.competitions = self.competitions + [new_comp]
        self.active_id = tournament_id

    def setup_league(
        self,
        name: str,
        players: list[str],
        sets_per_match: int = 3,
        games_per_set: int = 6,
    ) -> None:
        """Crea una NUEVA liga (no sobreescribe). Genera calendario aleatorio."""
        # Validación defensiva (la UI ya valida en ConfigState.save_config).
        if not name or not name.strip():
            return
        clean = [p.strip() for p in players if p.strip()]
        if len(clean) < 2:
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
        """Cierra un partido y, si es de torneo, propaga el ganador a la siguiente ronda."""
        target_match: Optional[LeagueMatch] = None
        target_comp: Optional[Competition] = None
        for comp in self.competitions:
            for m in comp.matches:
                if m.id == match_id:
                    target_match = m
                    target_comp = comp
                    break
            if target_match is not None:
                break

        if target_match is None or target_comp is None:
            return

        target_match.sets_home = sets_home
        target_match.sets_away = sets_away
        target_match.status = STATUS_FINALIZADO
        self.active_id = target_comp.id

        # Lógica de ascenso (solo para torneos eliminatorios).
        if (
            target_comp.competition_type == "tournament"
            and target_match.next_match_id is not None
            and target_match.bracket_position is not None
        ):
            winner = (
                target_match.home if sets_home > sets_away else target_match.away
            )
            if winner:
                next_match = next(
                    (x for x in target_comp.matches if x.id == target_match.next_match_id),
                    None,
                )
                if next_match is not None:
                    if target_match.bracket_position % 2 == 0:
                        next_match.home = winner
                    else:
                        next_match.away = winner
                    # Si ambos slots ya tienen jugadores reales (sin placeholders),
                    # quitamos el flag is_placeholder.
                    if (
                        next_match.home
                        and next_match.away
                        and not next_match.home.startswith("Ganador Partido")
                        and not next_match.away.startswith("Ganador Partido")
                    ):
                        next_match.is_placeholder = False

        # Reasignación para forzar reactividad de Reflex.
        self.competitions = list(self.competitions)

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
