"""
One-time script to seed fake leaderboard users into the database.
Run with: python seed_leaderboard.py
"""

import asyncio
import os
import json
from dotenv import load_dotenv
import db

load_dotenv()

# Fake users with realistic-looking non-round numbers
SEED_USERS = [
    {
        "user_id": "100000000000000001",
        "acorns": 4_873,
        "silver_acorns": 37,
        "emerald_acorns": 2,
        "golden_acorns": 0,
        "total_catches": 1_247,
        "junk_catches": 312,
        "level": 18,
        "xp": 1_340,
        "catches": json.dumps({
            "Grey Squirrel": 289, "Red Squirrel": 203, "Chipmunk": 176,
            "Eastern Squirrel": 112, "Park Squirrel": 98, "Bushy Tail": 87,
            "Acorn Hoarder": 64, "Tiny Squirrel": 53,
            "Black Squirrel": 42, "White Squirrel": 31, "Fox Squirrel": 28,
            "Pine Squirrel": 19, "Striped Squirrel": 14,
            "Flying Squirrel": 11, "Albino Squirrel": 8,
            "Giant Squirrel": 5, "Crystal Squirrel": 3,
            "Shadow Squirrel": 2, "Golden Squirrel": 1, "Arctic Squirrel": 1,
        }),
    },
    {
        "user_id": "100000000000000002",
        "acorns": 2_156,
        "silver_acorns": 19,
        "emerald_acorns": 1,
        "golden_acorns": 0,
        "total_catches": 843,
        "junk_catches": 198,
        "level": 14,
        "xp": 870,
        "catches": json.dumps({
            "Grey Squirrel": 201, "Red Squirrel": 148, "Chipmunk": 119,
            "Eastern Squirrel": 87, "Park Squirrel": 71, "Bushy Tail": 63,
            "Acorn Hoarder": 44, "Tiny Squirrel": 31,
            "Black Squirrel": 27, "Fox Squirrel": 18, "White Squirrel": 12,
            "Marsh Squirrel": 7, "Flying Squirrel": 6,
            "Albino Squirrel": 4, "Clockwork Squirrel": 3, "Crystal Squirrel": 2,
        }),
    },
    {
        "user_id": "100000000000000003",
        "acorns": 1_429,
        "silver_acorns": 11,
        "emerald_acorns": 0,
        "golden_acorns": 0,
        "total_catches": 587,
        "junk_catches": 156,
        "level": 11,
        "xp": 510,
        "catches": json.dumps({
            "Grey Squirrel": 156, "Red Squirrel": 98, "Chipmunk": 82,
            "Eastern Squirrel": 61, "Park Squirrel": 49, "Bushy Tail": 41,
            "Acorn Hoarder": 33, "Tiny Squirrel": 22,
            "Black Squirrel": 16, "Fox Squirrel": 11, "White Squirrel": 7,
            "Striped Squirrel": 4, "Flying Squirrel": 3,
            "Giant Squirrel": 2, "Albino Squirrel": 1, "Cinnamon Squirrel": 1,
        }),
    },
    {
        "user_id": "100000000000000004",
        "acorns": 763,
        "silver_acorns": 6,
        "emerald_acorns": 0,
        "golden_acorns": 0,
        "total_catches": 394,
        "junk_catches": 112,
        "level": 8,
        "xp": 290,
        "catches": json.dumps({
            "Grey Squirrel": 108, "Red Squirrel": 71, "Chipmunk": 54,
            "Eastern Squirrel": 42, "Park Squirrel": 36, "Bushy Tail": 29,
            "Acorn Hoarder": 21, "Tiny Squirrel": 14,
            "Black Squirrel": 8, "Fox Squirrel": 5, "White Squirrel": 3,
            "Pine Squirrel": 2, "Flying Squirrel": 1,
        }),
    },
    {
        "user_id": "100000000000000005",
        "acorns": 347,
        "silver_acorns": 2,
        "emerald_acorns": 0,
        "golden_acorns": 0,
        "total_catches": 213,
        "junk_catches": 67,
        "level": 5,
        "xp": 145,
        "catches": json.dumps({
            "Grey Squirrel": 62, "Red Squirrel": 41, "Chipmunk": 33,
            "Eastern Squirrel": 24, "Park Squirrel": 18, "Bushy Tail": 13,
            "Acorn Hoarder": 9, "Tiny Squirrel": 7,
            "Black Squirrel": 3, "Fox Squirrel": 2, "White Squirrel": 1,
        }),
    },
    {
        "user_id": "100000000000000006",
        "acorns": 184,
        "silver_acorns": 1,
        "emerald_acorns": 0,
        "golden_acorns": 0,
        "total_catches": 126,
        "junk_catches": 41,
        "level": 3,
        "xp": 78,
        "catches": json.dumps({
            "Grey Squirrel": 38, "Red Squirrel": 24, "Chipmunk": 19,
            "Eastern Squirrel": 14, "Park Squirrel": 11, "Bushy Tail": 8,
            "Acorn Hoarder": 5, "Tiny Squirrel": 4,
            "Black Squirrel": 2, "Fox Squirrel": 1,
        }),
    },
    {
        "user_id": "100000000000000007",
        "acorns": 91,
        "silver_acorns": 0,
        "emerald_acorns": 0,
        "golden_acorns": 0,
        "total_catches": 73,
        "junk_catches": 24,
        "level": 2,
        "xp": 42,
        "catches": json.dumps({
            "Grey Squirrel": 21, "Red Squirrel": 14, "Chipmunk": 12,
            "Eastern Squirrel": 8, "Park Squirrel": 7, "Bushy Tail": 5,
            "Acorn Hoarder": 3, "Tiny Squirrel": 2, "Black Squirrel": 1,
        }),
    },
]


async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        return

    await db.init_db(database_url)

    for user in SEED_USERS:
        uid = user.pop("user_id")
        catches_json = user.pop("catches")

        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO players (user_id, acorns, silver_acorns, emerald_acorns, golden_acorns,
                                     total_catches, junk_catches, level, xp, catches,
                                     trap_tier, junk_resist_tier, acorn_magnet_tier)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, 0, 0, 0)
                ON CONFLICT (user_id) DO UPDATE SET
                    acorns = EXCLUDED.acorns,
                    silver_acorns = EXCLUDED.silver_acorns,
                    emerald_acorns = EXCLUDED.emerald_acorns,
                    golden_acorns = EXCLUDED.golden_acorns,
                    total_catches = EXCLUDED.total_catches,
                    junk_catches = EXCLUDED.junk_catches,
                    level = EXCLUDED.level,
                    xp = EXCLUDED.xp,
                    catches = EXCLUDED.catches
                """,
                uid,
                user["acorns"],
                user["silver_acorns"],
                user["emerald_acorns"],
                user["golden_acorns"],
                user["total_catches"],
                user["junk_catches"],
                user["level"],
                user["xp"],
                catches_json,
            )
        print(f"Seeded user {uid} — Lvl {user['level']}, {user['total_catches']} catches")

    await db.close_db()
    print("\nDone! 7 users seeded.")


if __name__ == "__main__":
    asyncio.run(main())
