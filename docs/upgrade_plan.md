# SmartBets Pro — Upgrade Plan: Odds Watcher + Intelligence Signals + Alerts

## Current Architecture (Pre-Upgrade)

### Database Tables (11)
| Table | Purpose |
|---|---|
| sports | Sport definitions |
| leagues | League definitions |
| seasons | Seasons per league |
| teams | Team metadata |
| players | Player metadata |
| games | Game schedule + results |
| team_game_stats | Per-game team stats (JSONB) |
| player_game_stats | Per-game player stats (JSONB) |
| odds_snapshots | Bookmaker odds per market |
| predictions | Model predictions per market |
| overrides | Manual overrides (injury/lineup) |

### Services
| Service | Location | Purpose |
|---|---|---|
| PredictionService | services/prediction_service.py | Orchestrates feature build → model → predict |
| SoccerPoissonModel | services/prediction_models.py | Poisson-based soccer predictions |
| NBAModel | services/prediction_models.py | Regression-based NBA predictions |
| NHLModel | services/prediction_models.py | Poisson-based NHL predictions |
| TennisModel | services/prediction_models.py | ELO-based tennis predictions |
| BetBuilderService | services/rules_engine.py | Compatibility + correlation adjustment |
| BacktestService | services/backtest.py | Time-series backtesting |
| FeatureEngineering | services/features.py | TeamFeatures + PlayerFeatures computation |

### Endpoints (12)
| Endpoint | Purpose |
|---|---|
| GET /catalog/markets | Market catalog |
| GET /catalog/sports | Sports with market counts |
| GET /games | Games by date/sport/league |
| GET /games/{id} | Game detail |
| GET /odds | Odds for a game |
| GET /predictions | Model predictions |
| GET /best-bets | Value bets with edge |
| POST /builder/validate | Validate bet builder |
| GET /builder/suggestions | Auto builder combos |
| GET /reports/backtest | Backtest reports |
| POST /admin/overrides | Manual overrides |
| POST /jobs/ingest, /jobs/predict | Job triggers |

### Prediction Flow
```
GET /best-bets → PredictionService.generate_best_bets()
  → For each game:
    → _build_team_features(home/away)
    → predict_game() → sport-specific model
    → Match predictions vs bookmaker odds
    → Compute edge = (model_prob - implied_prob) / implied_prob × 100
    → Filter by min_edge, min_prob, min_conf
```

---

## New Architecture (Post-Upgrade)

### New Database Tables (+6)
| Table | Purpose |
|---|---|
| intelligence_signals | Detected signals (odds moves, lineup, segment, fatigue) |
| team_segment_profiles | Per-period offensive/defensive ratings |
| matchup_segment_profiles | H2H segment-level edge estimates |
| adjusted_predictions | Signal-adjusted predictions |
| notification_rules | User alert rules |
| notifications_sent | Alert delivery log + dedup |

### New Services (+4)
| Service | Location | Purpose |
|---|---|---|
| OddsWatcher | services/odds_watcher.py | Detect significant odds movements |
| SegmentProfileBuilder | services/segment_profiles.py | Build period-level team/matchup profiles |
| SignalAdjuster | services/signal_adjuster.py | Adjust base predictions using signals |
| AlertsEngine | services/alerts.py | Evaluate rules, dedup, emit notifications |

### New Endpoints (+5)
| Endpoint | Purpose |
|---|---|
| GET /signals | Intelligence signals for date/game |
| GET /odds/moves | Biggest odds movements |
| POST /notifications/rules | Create/update notification rules |
| GET /notifications/rules | List rules for user |
| GET /notifications/sent | Sent alerts for user |

### Updated Endpoints
| Endpoint | Change |
|---|---|
| GET /best-bets | Add `use_signals=true` param; return signals in response |

### New Enums
| Enum | Values |
|---|---|
| SignalType | ODDS_MOVE, LINEUP_CONFIRMED, KEY_PLAYER_OUT, MATCHUP_TREND, SEGMENT_DOMINANCE, FATIGUE_EDGE, REST_ADVANTAGE, SCHEDULE_PRESSURE, PLAYOFF_CONTEXT, SEASON_TREND |

### Signal-Adjusted Prediction Flow
```
GET /best-bets?use_signals=true
  → PredictionService.generate_best_bets() [existing]
  → For each game:
    → Fetch IntelligenceSignals for game
    → SignalAdjuster.adjust_prediction(base, signals)
      → Apply capped adjustments per signal type
      → Widen confidence interval
    → Store AdjustedPrediction
  → Return bets with signals + reasons
```

### Alert Flow
```
Celery: job_run_alerts() every 5 min
  → For each active NotificationRule:
    → Fetch adjusted predictions matching rule filters
    → Check: edge >= min_edge, conf >= min_conf
    → Check: at least 2 distinct signal types
    → Dedup: hash(game_id + market_key + line + selection + rule_id)
    → Cooldown: skip if sent within cooldown_minutes
    → Emit: store NotificationSent + log
```

### Frontend Changes
| Page | Change |
|---|---|
| / (Dashboard) | BetCard gets SignalsBadge |
| /game/[id] | New "Signals" tab |
| /alerts (NEW) | Alert history with filters |
| /odds-moves (NEW) | Odds movement tracker |
