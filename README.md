# SmartBets Pro

Sports analytics platform providing probability estimates, fair odds, and value identification across NBA, NHL, Soccer, and Tennis markets.

**DISCLAIMER: This platform provides statistical analysis and probability estimates only. These are NOT guarantees of outcomes. All sports betting involves risk and you may lose money. Never bet more than you can afford to lose. If you or someone you know has a gambling problem, call 1-800-522-4700.**

## Architecture

```
/apps/web          - Next.js 14 + TypeScript + Tailwind + TanStack Query
/apps/api          - FastAPI + Pydantic v2 + SQLAlchemy
/packages/shared   - Shared schemas, enums, market catalog (80+ markets)
/packages/fixtures - Mock data for offline development
docker-compose.yml - Full stack: API, Web, Postgres, Redis, Celery
```

## Quick Start

### Docker Compose (recommended)

```bash
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**API:**
```bash
cd apps/api
pip install -r requirements.txt
PYTHONPATH=../.. uvicorn apps.api.main:app --reload --port 8000
```

**Web:**
```bash
cd apps/web
npm install
npm run dev
```

## Market Coverage (80+ markets)

### Soccer (bookmaker-complete)
- 1X2 (FT/HT), Double Chance, Draw No Bet
- Totals O/U (0.5-5.5), Team Totals, BTTS, BTTS+O/U
- Correct Score, Winning Margin, Clean Sheet, Win to Nil
- Corners: Total, Team, Handicap, 1H, Race to N, Most, Exact
- Cards: Total, Team, Player Booked, Red Card, Handicap
- Shots/SOT: Total, Team, Player
- Player: Anytime Scorer, First/Last Scorer, Assists

### NBA (bookmaker-complete)
- Moneyline, Spread (alt lines), Totals (alt), Team Totals
- 1H/2H/Quarter Winners, Period Totals, Race to Points
- Player Props: Points, Rebounds, Assists, Threes, Steals, Blocks, Turnovers
- Combos: PRA, PR, PA, RA, Double-Double, Triple-Double
- First Basket, Milestones (20+/25+/30+)
- Team Props: Threes, Rebounds, Assists

### NHL (bookmaker-complete)
- Moneyline (incl. OT/SO), Puck Line, Totals, Team Totals
- Period Winners, Period Totals, Regulation Time 3-Way
- Player: Goals, Assists, Points, SOG, Goalie Saves, Anytime Scorer
- Team: SOG, Powerplay Goals

### Tennis
- Match Winner, Set Betting, Total Games, Games Handicap
- Set Totals, First Set Winner, Tiebreak Yes/No
- Player Aces O/U, Double Faults O/U

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /catalog/markets` | Market catalog with all definitions |
| `GET /catalog/sports` | Sports with market counts |
| `GET /games` | Games by date/sport/league |
| `GET /games/{id}` | Game detail |
| `GET /odds` | Odds for a game |
| `GET /predictions` | Model predictions |
| `GET /best-bets` | Value bets with edge |
| `POST /builder/validate` | Validate bet builder combo |
| `GET /builder/suggestions` | Auto-generated builder combos |
| `GET /reports/backtest` | Backtest report |
| `POST /admin/overrides` | Manual overrides (auth required) |
| `POST /jobs/ingest` | Trigger data ingestion |
| `POST /jobs/predict` | Trigger prediction run |

## Modeling Strategy

- **Soccer/NHL**: Poisson/NegBin for goals → derive totals, BTTS, correct score, corners, cards, shots
- **NBA**: Regression for team points (pace-adjusted) + Normal distribution for O/U
- **Tennis**: ELO (overall + surface) for match/set outcomes
- **Player Props**: Poisson (count stats) or regression (continuous stats)
- **Bet Builder**: Correlation-adjusted combined probabilities

## TODO: Real API Integration

Replace mock providers with real data sources:
- Schedule: ESPN API, TheSportsDB
- Stats: NBA API, NHL API, Football-Data.org
- Odds: The Odds API, Pinnacle
- Player: Transfermarkt (soccer), Basketball-Reference
