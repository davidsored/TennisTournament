"""Estado de competiciones — backed por Supabase vía rx.session().

Las mutaciones (crear liga/torneo, registrar resultado, eliminar) escriben a
PostgreSQL con add+commit. La hidratación (`_hydrate`) lee leagues, tournaments
y league_matches y construye las vistas pydantic transitorias que consumen los
componentes UI (CompetitionView / FixturePair / RoundView).
"""

from __future__ import annotations

import json
import random
from typing import Optional

import reflex as rx
from pydantic import BaseModel, Field
from sqlmodel import select

from ..logic.fixtures import FixtureMatch, group_fixtures
from ..logic.players import plan_rename
from ..logic.standings import MatchResult, compute_standings
from ..logic.validation import validate_competition_config
from ..logic.tournament_engine import (
    compute_bracket_size,
    distribute_byes,
    plan_bracket,
    propagate_winner,
)
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
    # Configuración de scoring desnormalizada — necesaria para que el marcador
    # cierre el set en el nº correcto de juegos (no asume 6 hardcoded).
    config_sets: int = 3
    config_games: int = 6


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
        # CRÍTICO: arrastrar la configuración de scoring para que el marcador
        # honre el `games_per_set` elegido por el usuario al crear la liga/torneo.
        config_sets=m.config_sets,
        config_games=m.config_games,
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
        # Defensa server-side: este handler es invocable directamente desde el
        # cliente, así que no basta con la validación del formulario.
        if validate_competition_config(name, players, sets_per_match, games_per_set):
            return
        clean = [p.strip() for p in players if p.strip()]

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
                            config_sets=sets_per_match,
                            config_games=games_per_set,
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
                            config_sets=sets_per_match,
                            config_games=games_per_set,
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
        """Crea un NUEVO torneo eliminatorio en Postgres con bracket completo.

        La planificación (sizing, BYEs, propagación, etiquetas locales) vive en
        `logic.tournament_engine` como funciones puras y testeables. Aquí solo
        orquestamos la persistencia: convertimos `BracketSlot` → `LeagueMatch`,
        commit, refresh y cableamos `next_match_id` con los ids reales.
        """
        # Defensa server-side (ver setup_league).
        if validate_competition_config(name, players, sets_per_match, games_per_set):
            return
        real = [p.strip() for p in players if p.strip()]

        random.shuffle(real)
        bracket_size = compute_bracket_size(len(real))
        seeding = distribute_byes(real, bracket_size)
        slots = plan_bracket(seeding, sets_per_match)

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

            # Insertar todos los slots como filas LeagueMatch (sin next_match_id).
            slot_to_match: dict[tuple[int, int], LeagueMatch] = {}
            db_matches: list[LeagueMatch] = []
            for s in slots:
                m = LeagueMatch(
                    tournament_id=tournament.id,
                    round_num=s.round_num,
                    leg=1,
                    home=s.home,
                    away=s.away,
                    status=s.status,
                    sets_home=s.sets_home,
                    sets_away=s.sets_away,
                    bracket_position=s.bracket_position,
                    is_placeholder=s.is_placeholder,
                    config_sets=sets_per_match,
                    config_games=games_per_set,
                )
                session.add(m)
                slot_to_match[(s.round_num, s.bracket_position)] = m
                db_matches.append(m)
            session.commit()
            for m in db_matches:
                session.refresh(m)

            # Cablear next_match_id con los ids reales asignados por Postgres.
            total_rounds = max(s.round_num for s in slots)
            for s in slots:
                if s.round_num >= total_rounds:
                    continue
                current = slot_to_match[(s.round_num, s.bracket_position)]
                next_target = slot_to_match[
                    (s.round_num + 1, s.bracket_position // 2)
                ]
                current.next_match_id = next_target.id
            session.commit()

            self.active_competition_id = tournament.id or 0
            self.active_competition_type = "tournament"

        self._hydrate()

    def record_result(
        self, match_id: int, sets_home: int, sets_away: int
    ) -> None:
        """Cierra un partido en DB y, si es de torneo, propaga el ganador.

        La lógica de "qué slot recibe al ganador y si quedan placeholders"
        vive en `logic.tournament_engine.propagate_winner` (función pura,
        testeable). Aquí sólo persistimos los cambios resultantes.
        """
        with rx.session() as session:
            m = session.get(LeagueMatch, match_id)
            if m is None:
                return

            m.sets_home = sets_home
            m.sets_away = sets_away
            m.status = STATUS_FINALIZADO

            if (
                m.tournament_id is not None
                and m.next_match_id is not None
                and m.bracket_position is not None
            ):
                winner = m.home if sets_home > sets_away else m.away
                if winner:
                    nxt = session.get(LeagueMatch, m.next_match_id)
                    if nxt is not None:
                        advanced = propagate_winner(
                            source_bracket_position=m.bracket_position,
                            winner_name=winner,
                            target_home=nxt.home,
                            target_away=nxt.away,
                            target_is_placeholder=nxt.is_placeholder,
                        )
                        nxt.home = advanced.home
                        nxt.away = advanced.away
                        nxt.is_placeholder = advanced.is_placeholder
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

    def rename_player(
        self, comp_id: int, comp_type: str, old_name: str, new_name: str
    ) -> str | None:
        """Renombra un participante en toda la competición. Transaccional.

        Actualiza `players_json` de la League/Tournament y los campos
        `home`/`away` de todos sus `league_matches` por igualdad EXACTA
        (así nunca toca placeholders "Ganador Partido N" ni BYEs). Un solo
        commit al final: o se aplica todo o no se aplica nada.

        Devuelve `None` si OK o un mensaje de error listo para la UI.
        """
        model = League if comp_type == "league" else Tournament

        with rx.session() as session:
            comp = session.get(model, comp_id)
            if comp is None:
                return "Competición no encontrada"

            players = _safe_players(comp.players_json)
            new_list, err = plan_rename(players, old_name, new_name)
            if err:
                return err

            # Los objetos vienen de la sesión: mutar atributos ya los marca
            # dirty, no hace falta session.add. Un único commit = atómico.
            comp.players_json = json.dumps(new_list)

            id_field = (
                LeagueMatch.league_id
                if comp_type == "league"
                else LeagueMatch.tournament_id
            )
            matches = session.exec(
                select(LeagueMatch).where(id_field == comp_id)
            ).all()
            clean_new = new_name.strip()
            for m in matches:
                if m.home == old_name:
                    m.home = clean_new
                if m.away == old_name:
                    m.away = clean_new

            session.commit()

        self._hydrate()
        return None

    async def delete_competition(self, comp_id: int, comp_type: str):
        """Elimina una competición y sus partidos. Requiere modo admin.

        El check vive aquí (y no sólo en la UI) porque cualquier handler
        público de un rx.State es invocable desde el cliente vía WebSocket.

        `comp_type` es obligatorio: `leagues` y `tournaments` tienen
        secuencias de id independientes, así que un id numérico solo no
        identifica la competición (una liga y un torneo pueden compartirlo).
        """
        from .admin_state import AdminState

        admin = await self.get_state(AdminState)
        if not admin.is_admin:
            return rx.toast.error(
                "Solo el administrador puede borrar competiciones"
            )
        try:
            cid = int(comp_id) if not isinstance(comp_id, int) else comp_id
        except (TypeError, ValueError):
            cid = 0
        if cid <= 0 or comp_type not in ("league", "tournament"):
            return rx.toast.error("Identificador de competición inválido")

        if comp_type == "league":
            model, id_field = League, LeagueMatch.league_id
        else:
            model, id_field = Tournament, LeagueMatch.tournament_id

        with rx.session() as session:
            for m in session.exec(
                select(LeagueMatch).where(id_field == cid)
            ).all():
                session.delete(m)
            comp = session.get(model, cid)
            if comp is not None:
                session.delete(comp)
            session.commit()

        if (
            self.active_competition_id == cid
            and self.active_competition_type == comp_type
        ):
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
        """Vista UI de la tabla. La matemática vive en `logic.standings`."""
        c = self._active()
        if not c or not c.players:
            return []

        results = [
            MatchResult(
                home=m.home,
                away=m.away,
                sets_home=m.sets_home,
                sets_away=m.sets_away,
                status=m.status,
            )
            for m in c.matches
        ]
        rows = compute_standings(c.players, results)

        return [
            {
                "pos": str(r.pos),
                "player": r.player,
                "pj": str(r.pj),
                "pg": str(r.pg),
                "pp": str(r.pp),
                "sets": f"{r.sets_won}-{r.sets_lost}",
                "pts": str(r.pts),
            }
            for r in rows
        ]

    # ---------------- Computed: fixtures agrupados ----------------

    @rx.var
    def grouped_fixtures(self) -> list[RoundView]:
        """Vista UI de los fixtures. El agrupamiento vive en `logic.fixtures`."""
        c = self._active()
        if not c:
            return []

        fx_input = [
            FixtureMatch(
                id=m.id,
                round_num=m.round_num,
                leg=m.leg,
                home=m.home,
                away=m.away,
                status=m.status,
                sets_home=m.sets_home,
                sets_away=m.sets_away,
            )
            for m in c.matches
        ]
        rounds_pure = group_fixtures(fx_input)

        out: list[RoundView] = []
        for r in rounds_pure:
            pairs: list[FixturePair] = []
            for p in r.pairs:
                pair = FixturePair()
                if p.ida is not None:
                    pair.has_ida = True
                    pair.ida_id = str(p.ida.match_id)
                    pair.ida_home = p.ida.home
                    pair.ida_away = p.ida.away
                    pair.ida_status = p.ida.status
                    pair.ida_sets_home = str(p.ida.sets_home)
                    pair.ida_sets_away = str(p.ida.sets_away)
                    pair.ida_home_winner = p.ida.home_winner
                    pair.ida_away_winner = p.ida.away_winner
                if p.vuelta is not None:
                    pair.has_vuelta = True
                    pair.vuelta_id = str(p.vuelta.match_id)
                    pair.vuelta_home = p.vuelta.home
                    pair.vuelta_away = p.vuelta.away
                    pair.vuelta_status = p.vuelta.status
                    pair.vuelta_sets_home = str(p.vuelta.sets_home)
                    pair.vuelta_sets_away = str(p.vuelta.sets_away)
                    pair.vuelta_home_winner = p.vuelta.home_winner
                    pair.vuelta_away_winner = p.vuelta.away_winner
                pairs.append(pair)
            out.append(RoundView(round_num=r.round_num, label=r.label, pairs=pairs))

        return out
