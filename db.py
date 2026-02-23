"""
Database module for Squirrel Catcher bot.
Uses asyncpg with PostgreSQL for persistent player data storage.
"""

import json
import asyncpg
from datetime import datetime, timezone, timedelta

pool: asyncpg.Pool | None = None

DEFAULT_PLAYER = {
    "acorns": 0,
    "silver_acorns": 0,
    "emerald_acorns": 0,
    "golden_acorns": 0,
    "catches": {},
    "total_catches": 0,
    "junk_catches": 0,
    "level": 1,
    "xp": 0,
    "last_daily": None,
    "trap_tier": 0,
    "junk_resist_tier": 0,
    "acorn_magnet_tier": 0,
}


async def init_db(database_url: str):
    """Create connection pool and ensure the players table exists."""
    global pool
    pool = await asyncpg.create_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                acorns INTEGER DEFAULT 0,
                silver_acorns INTEGER DEFAULT 0,
                emerald_acorns INTEGER DEFAULT 0,
                golden_acorns INTEGER DEFAULT 0,
                total_catches INTEGER DEFAULT 0,
                junk_catches INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                last_daily TIMESTAMPTZ,
                catches JSONB DEFAULT '{}'
            )
        """)
        # Add upgrade columns if they don't exist
        for col in ("trap_tier", "junk_resist_tier", "acorn_magnet_tier"):
            await conn.execute(f"""
                ALTER TABLE players ADD COLUMN IF NOT EXISTS {col} INTEGER DEFAULT 0
            """)
        # Create player_buffs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS player_buffs (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                buff_type TEXT NOT NULL,
                charges_left INTEGER,
                expires_at TIMESTAMPTZ,
                channel_id TEXT,
                last_triggered TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


def _row_to_dict(row: asyncpg.Record) -> dict:
    """Convert a database row to a player dict matching the old JSON format."""
    catches = row["catches"]
    if isinstance(catches, str):
        catches = json.loads(catches)
    return {
        "acorns": row["acorns"],
        "silver_acorns": row["silver_acorns"],
        "emerald_acorns": row["emerald_acorns"],
        "golden_acorns": row["golden_acorns"],
        "total_catches": row["total_catches"],
        "junk_catches": row["junk_catches"],
        "level": row["level"],
        "xp": row["xp"],
        "last_daily": row["last_daily"].isoformat() if row["last_daily"] else None,
        "catches": catches,
        "trap_tier": row["trap_tier"],
        "junk_resist_tier": row["junk_resist_tier"],
        "acorn_magnet_tier": row["acorn_magnet_tier"],
    }


async def get_player(user_id: str) -> dict:
    """Fetch a player by user_id. Creates a default row if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM players WHERE user_id = $1", user_id)
        if row is None:
            await conn.execute("INSERT INTO players (user_id) VALUES ($1)", user_id)
            return dict(DEFAULT_PLAYER)
        return _row_to_dict(row)


async def update_player(user_id: str, player: dict):
    """Upsert a player row from a player dict."""
    last_daily = None
    if player.get("last_daily"):
        ld = player["last_daily"]
        if isinstance(ld, str):
            dt = datetime.fromisoformat(ld)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            last_daily = dt
        else:
            last_daily = ld

    catches_json = json.dumps(player.get("catches", {}))

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO players (user_id, acorns, silver_acorns, emerald_acorns, golden_acorns,
                                 total_catches, junk_catches, level, xp, last_daily, catches,
                                 trap_tier, junk_resist_tier, acorn_magnet_tier)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13, $14)
            ON CONFLICT (user_id) DO UPDATE SET
                acorns = EXCLUDED.acorns,
                silver_acorns = EXCLUDED.silver_acorns,
                emerald_acorns = EXCLUDED.emerald_acorns,
                golden_acorns = EXCLUDED.golden_acorns,
                total_catches = EXCLUDED.total_catches,
                junk_catches = EXCLUDED.junk_catches,
                level = EXCLUDED.level,
                xp = EXCLUDED.xp,
                last_daily = EXCLUDED.last_daily,
                catches = EXCLUDED.catches,
                trap_tier = EXCLUDED.trap_tier,
                junk_resist_tier = EXCLUDED.junk_resist_tier,
                acorn_magnet_tier = EXCLUDED.acorn_magnet_tier
            """,
            user_id,
            player.get("acorns", 0),
            player.get("silver_acorns", 0),
            player.get("emerald_acorns", 0),
            player.get("golden_acorns", 0),
            player.get("total_catches", 0),
            player.get("junk_catches", 0),
            player.get("level", 1),
            player.get("xp", 0),
            last_daily,
            catches_json,
            player.get("trap_tier", 0),
            player.get("junk_resist_tier", 0),
            player.get("acorn_magnet_tier", 0),
        )


async def load_all_players() -> dict:
    """Load all players as a dict keyed by user_id (for leaderboard)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM players")
    return {row["user_id"]: _row_to_dict(row) for row in rows}


async def add_buff(user_id: str, buff_type: str, charges: int | None = None,
                   expires_at: datetime | None = None, channel_id: str | None = None) -> int:
    """Add a buff to a player. Returns the buff id."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO player_buffs (user_id, buff_type, charges_left, expires_at, channel_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_id, buff_type, charges, expires_at, channel_id,
        )
        return row["id"]


async def get_active_buffs(user_id: str) -> list[dict]:
    """Get all active buffs for a player (charges > 0 or not yet expired)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM player_buffs
            WHERE user_id = $1
              AND (charges_left IS NULL OR charges_left > 0)
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at
            """,
            user_id,
        )
    return [dict(r) for r in rows]


async def consume_buff_charge(buff_id: int):
    """Decrement charges_left for a buff. Delete if it hits 0."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE player_buffs SET charges_left = charges_left - 1 WHERE id = $1 RETURNING charges_left",
            buff_id,
        )
        if row and row["charges_left"] <= 0:
            await conn.execute("DELETE FROM player_buffs WHERE id = $1", buff_id)


async def cleanup_expired_buffs():
    """Delete expired time-based buffs."""
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM player_buffs WHERE expires_at IS NOT NULL AND expires_at <= NOW()"
        )


async def get_auto_catch_buffs() -> list[dict]:
    """Get all active auto-catch buffs (squirrel_hunter, elite_hunter)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM player_buffs
            WHERE buff_type IN ('squirrel_hunter', 'elite_hunter')
              AND expires_at > NOW()
            ORDER BY created_at
            """,
        )
    return [dict(r) for r in rows]


async def update_buff_last_triggered(buff_id: int):
    """Update the last_triggered timestamp for an auto-catch buff."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE player_buffs SET last_triggered = NOW() WHERE id = $1",
            buff_id,
        )


async def delete_buff(buff_id: int):
    """Delete a buff by id."""
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM player_buffs WHERE id = $1", buff_id)


async def close_db():
    """Close the connection pool."""
    global pool
    if pool:
        await pool.close()
        pool = None
