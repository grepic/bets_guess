"""Mock data providers using fixture data for offline development."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.game import GameInfo, OddsSnapshot, PlayerInfo, TeamInfo
from apps.api.providers.base import OddsProvider, ScheduleProvider, StatsProvider

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "fixtures"


def _load_json(sport: str, filename: str) -> list | dict:
    path = FIXTURES_DIR / sport / filename
    if path.exists():
        return json.loads(path.read_text())
    return []


class MockScheduleProvider(ScheduleProvider):
    async def get_games(
        self, sport: Sport, league: League | None = None, game_date: date | None = None,
    ) -> list[GameInfo]:
        raw = _load_json(sport.value, "games.json")
        games = []
        for g in raw:
            gi = GameInfo(
                game_id=g["game_id"],
                sport=Sport(g["sport"]),
                league=League(g["league"]),
                season=g.get("season", ""),
                home_team=TeamInfo(**g["home_team"]),
                away_team=TeamInfo(**g["away_team"]),
                start_time=datetime.fromisoformat(g["start_time"]),
                venue=g.get("venue", ""),
                is_playoff=g.get("is_playoff", False),
                status=g.get("status", "scheduled"),
            )
            if league and gi.league != league:
                continue
            if game_date and gi.start_time.date() != game_date:
                continue
            games.append(gi)
        return games

    async def get_game(self, game_id: str) -> GameInfo | None:
        for sport in Sport:
            raw = _load_json(sport.value, "games.json")
            for g in raw:
                if g["game_id"] == game_id:
                    return GameInfo(
                        game_id=g["game_id"],
                        sport=Sport(g["sport"]),
                        league=League(g["league"]),
                        season=g.get("season", ""),
                        home_team=TeamInfo(**g["home_team"]),
                        away_team=TeamInfo(**g["away_team"]),
                        start_time=datetime.fromisoformat(g["start_time"]),
                        venue=g.get("venue", ""),
                        is_playoff=g.get("is_playoff", False),
                        status=g.get("status", "scheduled"),
                    )
        return None

    async def get_teams(self, sport: Sport, league: League | None = None) -> list[TeamInfo]:
        raw = _load_json(sport.value, "teams.json")
        return [TeamInfo(**t) for t in raw]

    async def get_players(self, team_id: str) -> list[PlayerInfo]:
        for sport in Sport:
            raw = _load_json(sport.value, "players.json")
            return [PlayerInfo(**p) for p in raw if p.get("team_id") == team_id]
        return []


class MockStatsProvider(StatsProvider):
    async def get_team_stats(self, team_id: str, last_n: int = 10) -> list[dict]:
        for sport in Sport:
            raw = _load_json(sport.value, "team_stats.json")
            if isinstance(raw, dict):
                stats = raw.get(team_id, [])
            else:
                stats = [s for s in raw if s.get("team_id") == team_id]
            return stats[:last_n]
        return []

    async def get_player_stats(self, player_id: str, last_n: int = 10) -> list[dict]:
        for sport in Sport:
            raw = _load_json(sport.value, "player_stats.json")
            if isinstance(raw, dict):
                stats = raw.get(player_id, [])
            else:
                stats = [s for s in raw if s.get("player_id") == player_id]
            return stats[:last_n]
        return []

    async def get_team_season_stats(self, team_id: str, season_id: str) -> dict:
        for sport in Sport:
            raw = _load_json(sport.value, "team_season_stats.json")
            if isinstance(raw, dict) and team_id in raw:
                return raw[team_id]
        return {}

    async def get_head_to_head(
        self, team_a_id: str, team_b_id: str, last_n: int = 5,
    ) -> list[dict]:
        for sport in Sport:
            raw = _load_json(sport.value, "h2h.json")
            key = f"{team_a_id}_vs_{team_b_id}"
            key_alt = f"{team_b_id}_vs_{team_a_id}"
            if isinstance(raw, dict):
                return raw.get(key, raw.get(key_alt, []))[:last_n]
        return []


class MockOddsProvider(OddsProvider):
    async def get_odds(
        self, game_id: str, market_key: str | None = None,
    ) -> list[OddsSnapshot]:
        for sport in Sport:
            raw = _load_json(sport.value, "odds.json")
            odds = []
            for o in raw:
                if o.get("game_id") != game_id:
                    continue
                if market_key and o.get("market_key") != market_key:
                    continue
                odds.append(OddsSnapshot(
                    game_id=o["game_id"],
                    bookmaker=o.get("bookmaker", "mock_book"),
                    market_key=o["market_key"],
                    outcome_label=o["outcome_label"],
                    line=o.get("line"),
                    price=o["price"],
                    implied_prob=1.0 / o["price"] if o["price"] > 0 else None,
                    timestamp=datetime.fromisoformat(o["timestamp"]) if "timestamp" in o else datetime.utcnow(),
                ))
            if odds:
                return odds
        return []

    async def get_all_odds_for_date(
        self, sport: Sport, game_date: date,
    ) -> dict[str, list[OddsSnapshot]]:
        raw = _load_json(sport.value, "odds.json")
        result: dict[str, list[OddsSnapshot]] = {}
        for o in raw:
            snap = OddsSnapshot(
                game_id=o["game_id"],
                bookmaker=o.get("bookmaker", "mock_book"),
                market_key=o["market_key"],
                outcome_label=o["outcome_label"],
                line=o.get("line"),
                price=o["price"],
                implied_prob=1.0 / o["price"] if o["price"] > 0 else None,
            )
            result.setdefault(o["game_id"], []).append(snap)
        return result
