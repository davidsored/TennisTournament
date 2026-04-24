"""Tournament model: bracket eliminatorio."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .match import Match
from .player import Player


@dataclass
class Tournament:
    name: str
    players: list[Player] = field(default_factory=list)
    rounds: list[list[Match]] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def generate_bracket(self) -> None:
        """Genera el bracket eliminatorio (potencia de 2, con byes si hace falta)."""
        raise NotImplementedError
