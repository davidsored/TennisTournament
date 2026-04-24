"""League model: Round Robin doble vuelta."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .match import Match
from .player import Player


@dataclass
class League:
    name: str
    players: list[Player] = field(default_factory=list)
    matches: list[Match] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def generate_fixture(self) -> None:
        """Genera el calendario Round Robin x2 (ida y vuelta)."""
        raise NotImplementedError
