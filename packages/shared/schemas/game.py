from __future__ import annotations

import datetime as _dt
from datetime import date, datetime

from pydantic import BaseModel, Field

from packages.shared.enums.market import MarketGroup, Period
from packages.shared.enums.sport import League, Sport


class TeamInfo(BaseModel):
    team_id: str
    name: str
    short_name: str = ""
    logo_url: str = ""


class PlayerInfo(BaseModel):
    player_id: str
    name: str
    team_id: str
    position: str = ""
    jersey_number: int | None = None
    is_active: bool = True


class GameInfo(BaseModel):
    game_id: str
    sport: Sport
    league: League
    season: str = ""
    home_team: TeamInfo
    away_team: TeamInfo
    start_time: datetime
    venue: str = ""
    is_playoff: bool = False
    status: str = "scheduled"


class OddsSnapshot(BaseModel):
    game_id: str
    bookmaker: str
    market_key: str
    outcome_label: str
    line: float | None = None
    price: float
    implied_prob: float | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def compute_implied_prob(self) -> float:
        if self.price > 0:
            return 1.0 / self.price
        return 0.0


class OverrideRequest(BaseModel):
    game_id: str
    override_type: str  # "injury", "minutes", "lineup"
    player_id: str | None = None
    team_id: str | None = None
    key: str
    value: str
    note: str = ""


class FilterParams(BaseModel):
    date: _dt.date | None = None
    sport: Sport | None = None
    league: League | None = None
    market_group: MarketGroup | None = None
    period: Period | None = None
    min_edge: float = 0.0
    min_probability: float = 0.0
    min_confidence: float = 0.0
    hide_missing_odds: bool = False
    limit: int = 100
    offset: int = 0
