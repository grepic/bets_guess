"""Initial schema — all tables including intelligence signals layer.

Revision ID: 001
Revises: None
Create Date: 2026-02-09
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Core tables ──
    op.create_table(
        "sports",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("display_order", sa.Integer, default=0),
    )

    op.create_table(
        "leagues",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("sport_id", sa.String(32), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("country", sa.String(64), default=""),
        sa.Column("display_order", sa.Integer, default=0),
    )

    op.create_table(
        "seasons",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("league_id", sa.String(64), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("start_date", sa.DateTime, nullable=True),
        sa.Column("end_date", sa.DateTime, nullable=True),
        sa.Column("is_current", sa.Boolean, default=True),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("sport_id", sa.String(32), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("short_name", sa.String(32), default=""),
        sa.Column("logo_url", sa.String(512), default=""),
    )
    op.create_index("ix_teams_sport", "teams", ["sport_id"])

    op.create_table(
        "players",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("team_id", sa.String(64), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("position", sa.String(32), default=""),
        sa.Column("jersey_number", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
    )
    op.create_index("ix_players_team", "players", ["team_id"])

    op.create_table(
        "games",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("sport_id", sa.String(32), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("league_id", sa.String(64), sa.ForeignKey("leagues.id"), nullable=False),
        sa.Column("season_id", sa.String(64), sa.ForeignKey("seasons.id"), nullable=True),
        sa.Column("home_team_id", sa.String(64), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("away_team_id", sa.String(64), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("start_time", sa.DateTime, nullable=False),
        sa.Column("venue", sa.String(256), default=""),
        sa.Column("is_playoff", sa.Boolean, default=False),
        sa.Column("status", sa.String(32), default="scheduled"),
        sa.Column("home_score", sa.Integer, nullable=True),
        sa.Column("away_score", sa.Integer, nullable=True),
        sa.Column("result_data", postgresql.JSONB, default=dict),
    )
    op.create_index("ix_games_date", "games", ["start_time"])
    op.create_index("ix_games_sport_date", "games", ["sport_id", "start_time"])
    op.create_index("ix_games_league", "games", ["league_id"])

    op.create_table(
        "team_game_stats",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.String(64), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("team_id", sa.String(64), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("is_home", sa.Boolean, nullable=False),
        sa.Column("stats", postgresql.JSONB, default=dict),
        sa.UniqueConstraint("game_id", "team_id", name="uq_team_game_stats"),
    )
    op.create_index("ix_tgs_team", "team_game_stats", ["team_id"])

    op.create_table(
        "player_game_stats",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.String(64), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("player_id", sa.String(64), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("team_id", sa.String(64), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("minutes", sa.Float, nullable=True),
        sa.Column("started", sa.Boolean, default=False),
        sa.Column("stats", postgresql.JSONB, default=dict),
        sa.UniqueConstraint("game_id", "player_id", name="uq_player_game_stats"),
    )
    op.create_index("ix_pgs_player", "player_game_stats", ["player_id"])
    op.create_index("ix_pgs_game", "player_game_stats", ["game_id"])

    op.create_table(
        "odds_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.String(64), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("bookmaker", sa.String(64), nullable=False),
        sa.Column("market_key", sa.String(128), nullable=False),
        sa.Column("outcome_label", sa.String(64), nullable=False),
        sa.Column("line", sa.Float, nullable=True),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("implied_prob", sa.Float, nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_odds_game", "odds_snapshots", ["game_id"])
    op.create_index("ix_odds_market", "odds_snapshots", ["market_key"])
    op.create_index("ix_odds_game_market", "odds_snapshots", ["game_id", "market_key"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.String(64), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("market_key", sa.String(128), nullable=False),
        sa.Column("outcome_label", sa.String(64), nullable=False),
        sa.Column("line", sa.Float, nullable=True),
        sa.Column("probability", sa.Float, nullable=False),
        sa.Column("fair_odds", sa.Float, nullable=False),
        sa.Column("edge", sa.Float, nullable=True),
        sa.Column("interval_low", sa.Float, nullable=True),
        sa.Column("interval_high", sa.Float, nullable=True),
        sa.Column("model_version", sa.String(32), default="v1.0"),
        sa.Column("factors", postgresql.JSONB, default=list),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_pred_game", "predictions", ["game_id"])
    op.create_index("ix_pred_market", "predictions", ["market_key"])
    op.create_index("ix_pred_game_market", "predictions", ["game_id", "market_key"])

    op.create_table(
        "overrides",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("game_id", sa.String(64), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("override_type", sa.String(32), nullable=False),
        sa.Column("player_id", sa.String(64), nullable=True),
        sa.Column("team_id", sa.String(64), nullable=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("note", sa.Text, default=""),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("active", sa.Boolean, default=True),
    )
    op.create_index("ix_override_game", "overrides", ["game_id"])

    # ── Intelligence Signals layer ──
    op.create_table(
        "intelligence_signals",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("sport_id", sa.String(32), nullable=True),
        sa.Column("league_id", sa.String(64), nullable=True),
        sa.Column("game_id", sa.String(64), nullable=True),
        sa.Column("team_id", sa.String(64), nullable=True),
        sa.Column("player_id", sa.String(64), nullable=True),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("signal_strength", sa.Float, nullable=False, default=0.5),
        sa.Column("reliability", sa.Float, nullable=False, default=0.5),
        sa.Column("headline", sa.String(256), default=""),
        sa.Column("description", sa.Text, default=""),
        sa.Column("affected_market_groups", postgresql.JSONB, default=list),
        sa.Column("affected_periods", postgresql.JSONB, default=list),
        sa.Column("metadata", postgresql.JSONB, default=dict),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_signal_game", "intelligence_signals", ["game_id"])
    op.create_index("ix_signal_type", "intelligence_signals", ["signal_type"])
    op.create_index("ix_signal_created", "intelligence_signals", ["created_at"])
    op.create_index("ix_signal_game_type", "intelligence_signals", ["game_id", "signal_type"])

    op.create_table(
        "team_segment_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.String(64), nullable=False),
        sa.Column("segment_period", sa.String(16), nullable=False),
        sa.Column("offensive_rating", sa.Float, default=0.0),
        sa.Column("defensive_rating", sa.Float, default=0.0),
        sa.Column("net_rating", sa.Float, default=0.0),
        sa.Column("volatility", sa.Float, default=0.0),
        sa.Column("clutch_factor", sa.Float, default=0.0),
        sa.Column("sample_size", sa.Integer, default=0),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "segment_period", name="uq_team_segment"),
    )
    op.create_index("ix_tsp_team", "team_segment_profiles", ["team_id"])

    op.create_table(
        "matchup_segment_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("team_a_id", sa.String(64), nullable=False),
        sa.Column("team_b_id", sa.String(64), nullable=False),
        sa.Column("segment_period", sa.String(16), nullable=False),
        sa.Column("adjusted_edge_pp", sa.Float, default=0.0),
        sa.Column("h2h_weighted_effect_pp", sa.Float, default=0.0),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("style_tags", postgresql.JSONB, default=list),
        sa.Column("sample_size", sa.Integer, default=0),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("team_a_id", "team_b_id", "segment_period", name="uq_matchup_segment"),
    )
    op.create_index("ix_msp_teams", "matchup_segment_profiles", ["team_a_id", "team_b_id"])

    op.create_table(
        "adjusted_predictions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("base_prediction_id", sa.Integer, nullable=True),
        sa.Column("game_id", sa.String(64), nullable=False),
        sa.Column("market_key", sa.String(128), nullable=False),
        sa.Column("outcome_label", sa.String(64), nullable=False),
        sa.Column("base_prob", sa.Float, nullable=False),
        sa.Column("adjusted_prob", sa.Float, nullable=False),
        sa.Column("adjusted_fair_odds", sa.Float, nullable=False),
        sa.Column("adjusted_edge", sa.Float, nullable=True),
        sa.Column("interval_low", sa.Float, nullable=True),
        sa.Column("interval_high", sa.Float, nullable=True),
        sa.Column("applied_signal_ids", postgresql.JSONB, default=list),
        sa.Column("signal_reasons", postgresql.JSONB, default=list),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_apred_game", "adjusted_predictions", ["game_id"])
    op.create_index("ix_apred_game_market", "adjusted_predictions", ["game_id", "market_key"])

    op.create_table(
        "notification_rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_key", sa.String(128), nullable=False),
        sa.Column("sports", postgresql.JSONB, default=list),
        sa.Column("leagues", postgresql.JSONB, default=list),
        sa.Column("market_groups", postgresql.JSONB, default=list),
        sa.Column("min_edge", sa.Float, default=3.0),
        sa.Column("min_confidence", sa.Float, default=0.0),
        sa.Column("min_prob", sa.Float, default=0.0),
        sa.Column("quiet_hours", postgresql.JSONB, default=dict),
        sa.Column("max_alerts_per_game", sa.Integer, default=3),
        sa.Column("max_alerts_per_day", sa.Integer, default=20),
        sa.Column("cooldown_minutes", sa.Integer, default=30),
        sa.Column("enabled", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_nrule_user", "notification_rules", ["user_key"])

    op.create_table(
        "notifications_sent",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("notification_rules.id"), nullable=False),
        sa.Column("game_id", sa.String(64), nullable=False),
        sa.Column("market_key", sa.String(128), nullable=False),
        sa.Column("line", sa.Float, nullable=True),
        sa.Column("selection", sa.String(64), default=""),
        sa.Column("edge_pct", sa.Float, default=0.0),
        sa.Column("model_prob", sa.Float, default=0.0),
        sa.Column("fair_odds", sa.Float, default=0.0),
        sa.Column("signals_summary", postgresql.JSONB, default=list),
        sa.Column("payload", postgresql.JSONB, default=dict),
        sa.Column("sent_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("dedup_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_nsent_rule", "notifications_sent", ["rule_id"])
    op.create_index("ix_nsent_dedup", "notifications_sent", ["dedup_hash"])
    op.create_index("ix_nsent_game", "notifications_sent", ["game_id"])
    op.create_index("ix_nsent_sent", "notifications_sent", ["sent_at"])


def downgrade() -> None:
    op.drop_table("notifications_sent")
    op.drop_table("notification_rules")
    op.drop_table("adjusted_predictions")
    op.drop_table("matchup_segment_profiles")
    op.drop_table("team_segment_profiles")
    op.drop_table("intelligence_signals")
    op.drop_table("overrides")
    op.drop_table("predictions")
    op.drop_table("odds_snapshots")
    op.drop_table("player_game_stats")
    op.drop_table("team_game_stats")
    op.drop_table("games")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("seasons")
    op.drop_table("leagues")
    op.drop_table("sports")
