"""Abstract base classes for data providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.game import GameInfo, OddsSnapshot, PlayerInfo, TeamInfo


class ScheduleProvider(ABC):
    """Provides game schedule data."""

    @abstractmethod
    async def get_games(
        self, sport: Sport, league: League | None = None, game_date: date | None = None,
    ) -> list[GameInfo]:
        ...

    @abstractmethod
    async def get_game(self, game_id: str) -> GameInfo | None:
        ...

    @abstractmethod
    async def get_teams(self, sport: Sport, league: League | None = None) -> list[TeamInfo]:
        ...

    @abstractmethod
    async def get_players(self, team_id: str) -> list[PlayerInfo]:
        ...


class StatsProvider(ABC):
    """Provides team and player statistics."""

    @abstractmethod
    async def get_team_stats(
        self, team_id: str, last_n: int = 10,
    ) -> list[dict]:
        ...

    @abstractmethod
    async def get_player_stats(
        self, player_id: str, last_n: int = 10,
    ) -> list[dict]:
        ...

    @abstractmethod
    async def get_team_season_stats(self, team_id: str, season_id: str) -> dict:
        ...

    @abstractmethod
    async def get_head_to_head(
        self, team_a_id: str, team_b_id: str, last_n: int = 5,
    ) -> list[dict]:
        ...


class OddsProvider(ABC):
    """Provides odds data from bookmakers."""

    @abstractmethod
    async def get_odds(
        self, game_id: str, market_key: str | None = None,
    ) -> list[OddsSnapshot]:
        ...

    @abstractmethod
    async def get_all_odds_for_date(
        self, sport: Sport, game_date: date,
    ) -> dict[str, list[OddsSnapshot]]:
        ...
