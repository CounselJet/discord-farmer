"""
🐿️ Squirrel Catcher - A Discord Bot
Catch squirrels, earn acorns, and become the ultimate squirrel wrangler!
"""

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import random
import asyncio
from datetime import datetime, timedelta, timezone

import db

# ─── CONFIG ───────────────────────────────────────────────────────────────────

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PREFIX = "!sq "

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ─── CURRENCY ─────────────────────────────────────────────────────────────────

CURRENCIES = {
    "acorns": "🌰",
    "silver_acorns": "🥈🌰",
    "emerald_acorns": "💚🌰",
    "golden_acorns": "✨🌰",
}

EXCHANGE_RATES = {
    "acorns": 1,
    "silver_acorns": 100,
    "emerald_acorns": 1_000,
    "golden_acorns": 10_000,
}

# ─── SQUIRREL DATA ───────────────────────────────────────────────────────────

SQUIRRELS = [
    # (name, emoji, rarity, min_acorns, max_acorns, weight_chance)
    ("Grey Squirrel", "🐿️", "Common", 1, 5, 40),
    ("Red Squirrel", "🐿️", "Common", 2, 8, 30),
    ("Chipmunk", "🐿️", "Common", 1, 4, 35),
    ("Black Squirrel", "🖤🐿️", "Uncommon", 5, 15, 18),
    ("White Squirrel", "🤍🐿️", "Uncommon", 8, 20, 12),
    ("Fox Squirrel", "🦊🐿️", "Uncommon", 6, 18, 15),
    ("Flying Squirrel", "🪂🐿️", "Rare", 15, 40, 7),
    ("Albino Squirrel", "👻🐿️", "Rare", 20, 50, 5),
    ("Giant Squirrel", "💪🐿️", "Rare", 25, 60, 4),
    ("Crystal Squirrel", "💎🐿️", "Epic", 50, 120, 2),
    ("Shadow Squirrel", "🌑🐿️", "Epic", 60, 150, 1.5),
    ("Golden Squirrel", "👑🐿️", "Legendary", 150, 400, 0.5),
    ("Cosmic Squirrel", "🌌🐿️", "Legendary", 200, 500, 0.3),
    ("Mythic Nutcracker", "⚡🐿️", "Mythic", 500, 1200, 0.1),
]

RARITY_COLORS = {
    "Common": 0x808080,
    "Uncommon": 0x2ECC71,
    "Rare": 0x3498DB,
    "Epic": 0x9B59B6,
    "Legendary": 0xF1C40F,
    "Mythic": 0xE74C3C,
}

# ─── JUNK / NOTHING CATCHES ──────────────────────────────────────────────────

JUNK_CATCHES = [
    ("an empty acorn shell", "🥜", 0),
    ("a pinecone", "🌲", 1),
    ("a leaf", "🍂", 0),
    ("a stick", "🪵", 1),
    ("a muddy walnut", "💩", 2),
    ("a tiny mushroom", "🍄", 1),
    ("an old bird feather", "🪶", 1),
    ("a shiny pebble", "🪨", 2),
    ("nothing! The trap was empty", "💨", 0),
    ("a confused frog", "🐸", 3),
]

# ─── SHOP DATA ────────────────────────────────────────────────────────────────

SHOP_ITEMS = {
    "better_trap": {"name": "Better Trap", "emoji": "🪤", "cost": 500, "currency": "acorns",
                     "description": "-2s catch cooldown", "type": "upgrade", "upgrade_key": "trap_tier"},
    "squirrel_bait": {"name": "Squirrel Bait", "emoji": "🥜", "cost": 200, "currency": "acorns",
                       "description": "-5% junk chance (10 catches)", "type": "consumable", "charges": 10},
    "lucky_acorn": {"name": "Lucky Acorn", "emoji": "🍀", "cost": 1000, "currency": "acorns",
                     "description": "2x acorn rewards (30 min)", "type": "timed", "duration_minutes": 30},
    "rare_scent": {"name": "Rare Scent", "emoji": "✨", "cost": 2500, "currency": "acorns",
                    "description": "+3% Rare+ drop rate (20 catches)", "type": "consumable", "charges": 20},
    "squirrel_hunter": {"name": "Squirrel Hunter", "emoji": "🏹", "cost": 5000, "currency": "acorns",
                         "description": "Auto-catch every 30 min (24h)", "type": "auto_catch",
                         "interval_minutes": 30, "duration_hours": 24},
    "golden_bait": {"name": "Golden Bait", "emoji": "🥇", "cost": 1, "currency": "silver_acorns",
                     "description": "-10% junk chance (20 catches)", "type": "consumable", "charges": 20},
    "elite_hunter": {"name": "Elite Hunter", "emoji": "⚔️", "cost": 5, "currency": "silver_acorns",
                      "description": "Auto-catch every 15 min (24h)", "type": "auto_catch",
                      "interval_minutes": 15, "duration_hours": 24},
}

UPGRADE_TIERS = {
    "trap_tier": {"name": "Trap Speed", "max": 3,
                   "tiers": [{"cost": 500, "label": "8s cooldown"}, {"cost": 2000, "label": "6s cooldown"}, {"cost": 10000, "label": "5s cooldown"}]},
    "junk_resist_tier": {"name": "Junk Resistance", "max": 3,
                          "tiers": [{"cost": 1000, "label": "-3% junk"}, {"cost": 5000, "label": "-5% junk"}, {"cost": 20000, "label": "-8% junk"}]},
    "acorn_magnet_tier": {"name": "Acorn Magnet", "max": 3,
                           "tiers": [{"cost": 1500, "label": "+5% acorns"}, {"cost": 7500, "label": "+10% acorns"}, {"cost": 30000, "label": "+15% acorns"}]},
}

TRAP_COOLDOWNS = [10, 8, 6, 5]  # index = trap_tier
JUNK_RESIST_BONUSES = [0, 3, 5, 8]  # index = junk_resist_tier
ACORN_MAGNET_BONUSES = [0, 5, 10, 15]  # index = acorn_magnet_tier

# ─── COOLDOWNS ────────────────────────────────────────────────────────────────

CATCH_COOLDOWN = 10  # base seconds between catches
cooldowns: dict[int, datetime] = {}

# ─── LEVELING ─────────────────────────────────────────────────────────────────

def xp_for_level(level: int) -> int:
    return int(50 * (level ** 1.5))

def check_level_up(player: dict) -> bool:
    needed = xp_for_level(player["level"])
    if player["xp"] >= needed:
        player["xp"] -= needed
        player["level"] += 1
        return True
    return False

# ─── CATCH LOGIC ──────────────────────────────────────────────────────────────

def roll_catch(player_level: int, junk_resist_tier: int = 0,
               bait_junk_reduction: int = 0, has_rare_scent: bool = False) -> tuple:
    """Returns either a squirrel tuple or a junk tuple.
    junk_resist_tier: permanent junk reduction tier (0-3)
    bait_junk_reduction: temporary junk % reduction from bait buffs
    has_rare_scent: whether rare_scent buff is active
    """
    # 30% chance of junk, decreasing slightly with level
    junk_chance = max(5, 30 - player_level - JUNK_RESIST_BONUSES[junk_resist_tier] - bait_junk_reduction)
    if random.randint(1, 100) <= junk_chance:
        return ("junk", random.choice(JUNK_CATCHES))

    # Weighted random squirrel selection
    # Higher level = slightly better luck
    level_bonus = min(player_level * 0.5, 10)
    rare_bonus = 3 if has_rare_scent else 0
    weights = []
    for sq in SQUIRRELS:
        w = sq[5]
        # Boost rare+ squirrels slightly based on level
        if sq[2] in ("Rare", "Epic", "Legendary", "Mythic"):
            w *= (1 + (level_bonus + rare_bonus) / 100)
        weights.append(w)

    chosen = random.choices(SQUIRRELS, weights=weights, k=1)[0]
    acorns = random.randint(chosen[3], chosen[4])

    # Level bonus to acorns
    acorns = int(acorns * (1 + player_level * 0.02))

    return ("squirrel", chosen, acorns)

# ─── MENU VIEW ───────────────────────────────────────────────────────────────

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(discord.ui.Button(label="Donate", style=discord.ButtonStyle.link, emoji="💛", url="https://ko-fi.com/squirrelcatcher", row=0))

    @discord.ui.button(label="Catch!", style=discord.ButtonStyle.green, emoji="🪤", row=0)
    async def catch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_catch(interaction)

    @discord.ui.button(label="Bag", style=discord.ButtonStyle.primary, emoji="🎒", row=0)
    async def bag_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_bag(interaction)

    @discord.ui.button(label="Balance", style=discord.ButtonStyle.primary, emoji="💰", row=0)
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_balance(interaction)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.primary, emoji="🐿️", row=0)
    async def profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await do_profile(interaction)

    @discord.ui.select(
        placeholder="More actions...",
        options=[
            discord.SelectOption(label="Shop", value="shop", emoji="🛒"),
            discord.SelectOption(label="Active Buffs", value="buffs", emoji="⚡"),
            discord.SelectOption(label="Daily Bonus", value="daily", emoji="🎁"),
            discord.SelectOption(label="Bestiary", value="bestiary", emoji="📖"),
            discord.SelectOption(label="Leaderboard", value="leaderboard", emoji="🏆"),
            discord.SelectOption(label="Exchange Rates", value="exchange", emoji="🔄"),
            discord.SelectOption(label="Help", value="help", emoji="❓"),
        ],
        row=1,
    )
    async def menu_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        if choice == "shop":
            await do_shop(interaction)
        elif choice == "buffs":
            await do_buffs(interaction)
        elif choice == "daily":
            await do_daily(interaction)
        elif choice == "bestiary":
            await do_bestiary(interaction)
        elif choice == "leaderboard":
            await do_leaderboard(interaction)
        elif choice == "exchange":
            await do_exchange_info(interaction)
        elif choice == "help":
            await do_help(interaction)


async def _send(ctx_or_interaction, embed, view=None, ephemeral=False):
    """Send an embed from either a command context or interaction."""
    v = view or MenuView()
    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(embed=embed, view=v, ephemeral=ephemeral)
    else:
        await ctx_or_interaction.send(embed=embed, view=v)


async def do_catch(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    user_id = str(user.id)

    player = await db.get_player(user_id)

    # Cooldown check (reduced by trap_tier)
    cd_seconds = TRAP_COOLDOWNS[player.get("trap_tier", 0)]
    now = datetime.now()
    if user_id in cooldowns:
        diff = (cooldowns[user_id] - now).total_seconds()
        if diff > 0:
            msg = f"⏳ Your trap is recharging! Try again in **{diff:.0f}s**."
            if is_interaction:
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return

    cooldowns[user_id] = now + timedelta(seconds=cd_seconds)

    # Gather active buffs
    active_buffs = await db.get_active_buffs(user_id)
    bait_junk_reduction = 0
    bait_buff_id = None
    has_rare_scent = False
    rare_scent_buff_id = None
    has_lucky_acorn = False

    for buff in active_buffs:
        bt = buff["buff_type"]
        if bt == "squirrel_bait":
            bait_junk_reduction = 5
            bait_buff_id = buff["id"]
        elif bt == "golden_bait":
            bait_junk_reduction = 10
            bait_buff_id = buff["id"]
        elif bt == "rare_scent":
            has_rare_scent = True
            rare_scent_buff_id = buff["id"]
        elif bt == "lucky_acorn":
            has_lucky_acorn = True

    # Suspense message
    if is_interaction:
        await ctx_or_interaction.response.send_message("🪤 Setting your trap in the forest...")
        msg = await ctx_or_interaction.original_response()
    else:
        msg = await ctx_or_interaction.send("🪤 Setting your trap in the forest...")
    await asyncio.sleep(1.5)

    result = roll_catch(player["level"], player.get("junk_resist_tier", 0),
                        bait_junk_reduction, has_rare_scent)

    # Consume charge-based buffs that were used
    if bait_buff_id is not None:
        await db.consume_buff_charge(bait_buff_id)
    if rare_scent_buff_id is not None:
        await db.consume_buff_charge(rare_scent_buff_id)

    if result[0] == "junk":
        _, (junk_name, junk_emoji, junk_acorns) = result
        player["junk_catches"] += 1
        player["acorns"] += junk_acorns
        player["xp"] += 1

        embed = discord.Embed(
            title=f"{junk_emoji} You caught... {junk_name}!",
            description=f"Better luck next time!" + (f"\nBut you found **{junk_acorns}** 🌰!" if junk_acorns > 0 else ""),
            color=0x95A5A6,
        )
    else:
        _, squirrel, acorns = result
        sq_name, sq_emoji, sq_rarity, _, _, _ = squirrel

        # Apply acorn bonuses
        magnet_bonus = ACORN_MAGNET_BONUSES[player.get("acorn_magnet_tier", 0)]
        acorns = int(acorns * (1 + magnet_bonus / 100))
        if has_lucky_acorn:
            acorns *= 2

        player["acorns"] += acorns
        player["total_catches"] += 1
        player["catches"][sq_name] = player["catches"].get(sq_name, 0) + 1

        xp_gain = {"Common": 5, "Uncommon": 10, "Rare": 20, "Epic": 40, "Legendary": 80, "Mythic": 200}
        player["xp"] += xp_gain.get(sq_rarity, 5)

        embed = discord.Embed(
            title=f"{sq_emoji} You caught a {sq_name}!",
            description=f"**Rarity:** {sq_rarity}\n**Reward:** {acorns} 🌰",
            color=RARITY_COLORS.get(sq_rarity, 0x808080),
        )

        if has_lucky_acorn:
            embed.description += " (2x Lucky Acorn!)"
        if sq_rarity in ("Epic", "Legendary", "Mythic"):
            embed.set_footer(text=f"🎉 Wow! A {sq_rarity} catch!")

    leveled = check_level_up(player)
    if leveled:
        embed.add_field(name="🎉 LEVEL UP!", value=f"You are now **Level {player['level']}**!", inline=False)

    await db.update_player(user_id, player)
    await msg.edit(content=None, embed=embed, view=MenuView())


async def do_bag(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))
    catches = player.get("catches", {})

    if not catches:
        embed = discord.Embed(
            title=f"🎒 {user.display_name}'s Squirrel Bag",
            description="Your bag is empty! Hit **Catch** to start!",
            color=0x8B4513,
        )
    else:
        sorted_catches = sorted(catches.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for name, count in sorted_catches:
            sq_data = next((s for s in SQUIRRELS if s[0] == name), None)
            if sq_data:
                lines.append(f"{sq_data[1]} **{name}** ({sq_data[2]}) x{count}")
        embed = discord.Embed(
            title=f"🎒 {user.display_name}'s Squirrel Bag",
            description="\n".join(lines),
            color=0x8B4513,
        )
        embed.set_footer(text=f"Total unique species: {len(catches)} / {len(SQUIRRELS)}")

    await _send(ctx_or_interaction, embed)


async def do_balance(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    lines = []
    for currency, emoji in CURRENCIES.items():
        amount = player.get(currency, 0)
        nice_name = currency.replace("_", " ").title()
        lines.append(f"{emoji} **{nice_name}:** {amount:,}")

    total = sum(player.get(c, 0) * r for c, r in EXCHANGE_RATES.items())
    embed = discord.Embed(
        title=f"💰 {user.display_name}'s Acorn Stash",
        description="\n".join(lines),
        color=0xF39C12,
    )
    embed.set_footer(text=f"Total value: {total:,} acorns")
    await _send(ctx_or_interaction, embed)


async def do_profile(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))
    xp_needed = xp_for_level(player["level"])

    embed = discord.Embed(title=f"🐿️ {user.display_name}'s Profile", color=0x8B4513)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Level", value=f"**{player['level']}** ({player['xp']}/{xp_needed} XP)", inline=True)
    embed.add_field(name="Total Catches", value=f"🐿️ {player['total_catches']}", inline=True)
    embed.add_field(name="Junk Catches", value=f"🗑️ {player['junk_catches']}", inline=True)
    bal_lines = [f"{e} {player.get(c, 0):,}" for c, e in CURRENCIES.items()]
    embed.add_field(name="Acorn Stash", value=" | ".join(bal_lines), inline=False)
    unique = len(player.get("catches", {}))
    embed.add_field(name="Bestiary", value=f"📖 {unique}/{len(SQUIRRELS)} species discovered", inline=False)
    await _send(ctx_or_interaction, embed)


async def do_daily(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    user_id = str(user.id)
    player = await db.get_player(user_id)

    last_daily = player.get("last_daily", None)
    now = datetime.now()

    if last_daily:
        last = datetime.fromisoformat(last_daily)
        if (now - last).total_seconds() < 86400:
            remaining = 86400 - (now - last).total_seconds()
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            embed = discord.Embed(
                title="⏳ Daily Already Claimed",
                description=f"Come back in **{hours}h {mins}m**.",
                color=0x95A5A6,
            )
            await _send(ctx_or_interaction, embed)
            return

    reward = 50 + (player["level"] * 10)
    player["acorns"] += reward
    player["last_daily"] = now.isoformat()
    await db.update_player(user_id, player)

    embed = discord.Embed(
        title="🎁 Daily Bonus Claimed!",
        description=f"You received **{reward}** 🌰 acorns!\n(Level {player['level']} bonus)",
        color=0x2ECC71,
    )
    await _send(ctx_or_interaction, embed)


async def do_bestiary(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))
    catches = player.get("catches", {})

    lines = []
    for sq in SQUIRRELS:
        name, emoji, rarity, _, _, _ = sq
        if name in catches:
            lines.append(f"{emoji} **{name}** — {rarity} ✅ (x{catches[name]})")
        else:
            lines.append(f"❓ **???** — {rarity}")

    embed = discord.Embed(title="📖 Squirrel Bestiary", description="\n".join(lines), color=0x8B4513)
    embed.set_footer(text=f"Discovered: {len(catches)}/{len(SQUIRRELS)}")
    await _send(ctx_or_interaction, embed)


async def do_leaderboard(ctx_or_interaction):
    data = await db.load_all_players()
    if not data:
        embed = discord.Embed(title="🏆 Leaderboard", description="No squirrel catchers yet!", color=0xF1C40F)
        await _send(ctx_or_interaction, embed)
        return

    rankings = []
    for uid, player in data.items():
        total = sum(player.get(c, 0) * r for c, r in EXCHANGE_RATES.items())
        rankings.append((uid, total, player.get("total_catches", 0), player.get("level", 1)))
    rankings.sort(key=lambda x: x[1], reverse=True)

    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, total, catches, level) in enumerate(rankings[:10]):
        medal = medals[i] if i < 3 else f"**{i+1}.**"
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except Exception:
            name = f"User {uid[:6]}"
        lines.append(f"{medal} **{name}** — Lvl {level} | {total:,} 🌰 | {catches} catches")

    embed = discord.Embed(title="🏆 Squirrel Catcher Leaderboard", description="\n".join(lines), color=0xF1C40F)
    await _send(ctx_or_interaction, embed)


async def do_exchange_info(ctx_or_interaction):
    embed = discord.Embed(
        title="🔄 Exchange Rates",
        description=(
            "• 100 🌰 Acorns → 1 🥈🌰 Silver Acorn\n"
            "• 10 🥈🌰 Silver Acorns → 1 💚🌰 Emerald Acorn\n"
            "• 10 💚🌰 Emerald Acorns → 1 ✨🌰 Golden Acorn\n\n"
            f"Use `{PREFIX}exchange <amount>` to convert."
        ),
        color=0x3498DB,
    )
    await _send(ctx_or_interaction, embed)


async def do_help(ctx_or_interaction):
    embed = discord.Embed(
        title="🐿️ Squirrel Catcher - Commands",
        description="Catch squirrels, earn acorns, become the ultimate wrangler!",
        color=0x8B4513,
    )
    cmds = [
        (f"`{PREFIX}catch`", "Set a trap and try to catch a squirrel!"),
        (f"`{PREFIX}bag`", "View your caught squirrels"),
        (f"`{PREFIX}balance`", "Check your acorn stash"),
        (f"`{PREFIX}profile`", "View your full profile"),
        (f"`{PREFIX}shop`", "Browse items and upgrades"),
        (f"`{PREFIX}buy <item>`", "Purchase an item or upgrade"),
        (f"`{PREFIX}buffs`", "View your active buffs and upgrades"),
        (f"`{PREFIX}exchange <amount>`", "Convert 100 acorns → 1 silver acorn, etc."),
        (f"`{PREFIX}leaderboard`", "See the top squirrel catchers"),
        (f"`{PREFIX}bestiary`", "View all discoverable squirrels"),
        (f"`{PREFIX}sell <squirrel name>`", "Sell a squirrel from your bag"),
        (f"`{PREFIX}daily`", "Claim your daily acorn bonus"),
    ]
    for name, desc in cmds:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="Or just use the buttons and menu below! 🌰")
    await _send(ctx_or_interaction, embed)


async def do_shop(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    embed = discord.Embed(title="🛒 Squirrel Shop", color=0xE67E22)

    # Items & Buffs section
    item_lines = []
    for key, item in SHOP_ITEMS.items():
        if item["type"] == "upgrade":
            continue
        currency_emoji = CURRENCIES.get(item["currency"], "🌰")
        item_lines.append(f"{item['emoji']} **{item['name']}** — {item['cost']:,} {currency_emoji}\n  _{item['description']}_\n  `!sq buy {key}`")
    embed.add_field(name="Items & Buffs", value="\n".join(item_lines), inline=False)

    # Permanent Upgrades section
    upgrade_lines = []
    for key, upgrade in UPGRADE_TIERS.items():
        current_tier = player.get(key, 0)
        tier_display = []
        for i, tier in enumerate(upgrade["tiers"]):
            if i < current_tier:
                tier_display.append(f"  ~~Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)~~ ✅")
            elif i == current_tier:
                tier_display.append(f"  **Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)** ← Next")
            else:
                tier_display.append(f"  Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)")
        if current_tier >= upgrade["max"]:
            upgrade_lines.append(f"🪤 **{upgrade['name']}** — MAX ✅")
        else:
            upgrade_lines.append(f"🪤 **{upgrade['name']}**\n" + "\n".join(tier_display))
    embed.add_field(name="Permanent Upgrades", value="\n".join(upgrade_lines), inline=False)

    embed.set_footer(text=f"Use !sq buy <item> to purchase")
    await _send(ctx_or_interaction, embed)


async def do_buy(ctx_or_interaction, item_key: str):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    user_id = str(user.id)
    player = await db.get_player(user_id)

    # Check if it's an upgrade tier purchase
    if item_key in UPGRADE_TIERS:
        upgrade = UPGRADE_TIERS[item_key]
        current_tier = player.get(item_key, 0)
        if current_tier >= upgrade["max"]:
            msg = f"❌ **{upgrade['name']}** is already at max tier!"
            if is_interaction:
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return
        tier_cost = upgrade["tiers"][current_tier]["cost"]
        if player["acorns"] < tier_cost:
            msg = f"❌ You need **{tier_cost:,}** 🌰 for {upgrade['name']} Tier {current_tier + 1}! (You have {player['acorns']:,})"
            if is_interaction:
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return
        player["acorns"] -= tier_cost
        player[item_key] = current_tier + 1
        await db.update_player(user_id, player)
        tier_label = upgrade["tiers"][current_tier]["label"]
        embed = discord.Embed(
            title=f"🪤 Upgraded {upgrade['name']}!",
            description=f"**Tier {current_tier + 1}:** {tier_label}\nCost: {tier_cost:,} 🌰",
            color=0x2ECC71,
        )
        await _send(ctx_or_interaction, embed)
        return

    # Check shop items
    if item_key not in SHOP_ITEMS:
        msg = f"❌ Unknown item: **{item_key}**. Use `!sq shop` to see available items."
        if is_interaction:
            await ctx_or_interaction.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)
        return

    item = SHOP_ITEMS[item_key]

    # For upgrade-type shop items, redirect to upgrade logic
    if item["type"] == "upgrade":
        await do_buy(ctx_or_interaction, item["upgrade_key"])
        return

    # Check currency
    currency = item["currency"]
    cost = item["cost"]
    if player[currency] < cost:
        currency_emoji = CURRENCIES.get(currency, "🌰")
        msg = f"❌ You need **{cost:,}** {currency_emoji}! (You have {player[currency]:,})"
        if is_interaction:
            await ctx_or_interaction.response.send_message(msg, ephemeral=True)
        else:
            await ctx_or_interaction.send(msg)
        return

    # Deduct cost
    player[currency] -= cost
    await db.update_player(user_id, player)

    # Create buff
    channel_id = str(ctx_or_interaction.channel_id) if hasattr(ctx_or_interaction, "channel_id") else None
    if not channel_id and hasattr(ctx_or_interaction, "channel"):
        channel_id = str(ctx_or_interaction.channel.id)

    if item["type"] == "consumable":
        await db.add_buff(user_id, item_key, charges=item["charges"])
    elif item["type"] == "timed":
        expires = datetime.now(timezone.utc) + timedelta(minutes=item["duration_minutes"])
        await db.add_buff(user_id, item_key, expires_at=expires)
    elif item["type"] == "auto_catch":
        expires = datetime.now(timezone.utc) + timedelta(hours=item["duration_hours"])
        await db.add_buff(user_id, item_key, expires_at=expires, channel_id=channel_id)

    currency_emoji = CURRENCIES.get(currency, "🌰")
    embed = discord.Embed(
        title=f"{item['emoji']} Purchased {item['name']}!",
        description=f"{item['description']}\nCost: {cost:,} {currency_emoji}",
        color=0x2ECC71,
    )
    await _send(ctx_or_interaction, embed)


async def do_buffs(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    user_id = str(user.id)
    player = await db.get_player(user_id)
    active_buffs = await db.get_active_buffs(user_id)

    embed = discord.Embed(title=f"⚡ {user.display_name}'s Active Buffs", color=0x9B59B6)

    # Active consumable/timed buffs
    if active_buffs:
        buff_lines = []
        for buff in active_buffs:
            item = SHOP_ITEMS.get(buff["buff_type"])
            if not item:
                continue
            emoji = item["emoji"]
            name = item["name"]
            if buff["charges_left"] is not None:
                buff_lines.append(f"{emoji} **{name}** — {buff['charges_left']} charges left")
            elif buff["expires_at"]:
                remaining = buff["expires_at"] - datetime.now(timezone.utc)
                if remaining.total_seconds() > 0:
                    mins = int(remaining.total_seconds() // 60)
                    hrs = mins // 60
                    mins = mins % 60
                    time_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"
                    buff_lines.append(f"{emoji} **{name}** — {time_str} remaining")
        if buff_lines:
            embed.add_field(name="Active Buffs", value="\n".join(buff_lines), inline=False)
        else:
            embed.add_field(name="Active Buffs", value="None", inline=False)
    else:
        embed.add_field(name="Active Buffs", value="No active buffs. Visit `!sq shop` to buy some!", inline=False)

    # Permanent upgrades
    upgrade_lines = []
    for key, upgrade in UPGRADE_TIERS.items():
        current = player.get(key, 0)
        if current > 0:
            label = upgrade["tiers"][current - 1]["label"]
            upgrade_lines.append(f"🪤 **{upgrade['name']}** Tier {current}: {label}")
    if upgrade_lines:
        embed.add_field(name="Permanent Upgrades", value="\n".join(upgrade_lines), inline=False)
    else:
        embed.add_field(name="Permanent Upgrades", value="None yet. Visit `!sq shop`!", inline=False)

    await _send(ctx_or_interaction, embed)


# ─── AUTO-CATCH BACKGROUND TASK ──────────────────────────────────────────────

@tasks.loop(minutes=1)
async def auto_catch_tick():
    """Process auto-catch buffs every minute."""
    try:
        auto_buffs = await db.get_auto_catch_buffs()
    except Exception:
        return

    now = datetime.now(timezone.utc)

    for buff in auto_buffs:
        item = SHOP_ITEMS.get(buff["buff_type"])
        if not item:
            continue

        interval = timedelta(minutes=item["interval_minutes"])
        last = buff.get("last_triggered")

        if last is not None and (now - last) < interval:
            continue

        # Time to auto-catch
        user_id = buff["user_id"]
        player = await db.get_player(user_id)

        result = roll_catch(player["level"], player.get("junk_resist_tier", 0))

        if result[0] == "junk":
            _, (junk_name, junk_emoji, junk_acorns) = result
            player["junk_catches"] += 1
            player["acorns"] += junk_acorns
            player["xp"] += 1
        else:
            _, squirrel, acorns = result
            sq_name, sq_emoji, sq_rarity, _, _, _ = squirrel
            magnet_bonus = ACORN_MAGNET_BONUSES[player.get("acorn_magnet_tier", 0)]
            acorns = int(acorns * (1 + magnet_bonus / 100))
            player["acorns"] += acorns
            player["total_catches"] += 1
            player["catches"][sq_name] = player["catches"].get(sq_name, 0) + 1
            xp_gain = {"Common": 5, "Uncommon": 10, "Rare": 20, "Epic": 40, "Legendary": 80, "Mythic": 200}
            player["xp"] += xp_gain.get(sq_rarity, 5)

        check_level_up(player)
        await db.update_player(user_id, player)
        await db.update_buff_last_triggered(buff["id"])

    # Clean up expired buffs and send summary messages
    await _check_expired_auto_catch()
    await db.cleanup_expired_buffs()


async def _check_expired_auto_catch():
    """Check for auto-catch buffs that just expired and send summary."""
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM player_buffs
                WHERE buff_type IN ('squirrel_hunter', 'elite_hunter')
                  AND expires_at IS NOT NULL AND expires_at <= NOW()
                  AND channel_id IS NOT NULL
                """
            )
        for row in rows:
            channel_id = row["channel_id"]
            user_id = row["user_id"]
            try:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    item = SHOP_ITEMS.get(row["buff_type"], {})
                    embed = discord.Embed(
                        title=f"{item.get('emoji', '🏹')} Auto-Catch Complete!",
                        description=f"<@{user_id}>'s **{item.get('name', 'Auto-Catch')}** has expired. Check your bag for the results!",
                        color=0xE67E22,
                    )
                    await channel.send(embed=embed)
            except Exception:
                pass
    except Exception:
        pass


@auto_catch_tick.before_loop
async def before_auto_catch():
    await bot.wait_until_ready()


# ─── BOT EVENTS ───────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    await db.init_db(DATABASE_URL)
    if not auto_catch_tick.is_running():
        auto_catch_tick.start()
    print(f"🐿️ Squirrel Catcher is online as {bot.user}!")
    print(f"   Prefix: {PREFIX}")
    print(f"   Servers: {len(bot.guilds)}")
    print(f"   Database: connected")
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help | 🐿️"))


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Send a welcome message with the menu when the bot joins a new server."""
    # Find the first text channel the bot can send messages in
    channel = None
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        channel = guild.system_channel
    else:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break

    if channel is None:
        return

    embed = discord.Embed(
        title="🐿️ Squirrel Catcher has arrived!",
        description=(
            "Catch squirrels, earn acorns, and compete with your friends!\n\n"
            "Use the **buttons** below or type commands with `!sq`.\n"
            "Hit **Catch** to set your first trap!"
        ),
        color=0x8B4513,
    )
    embed.add_field(
        name="Quick Start",
        value=(
            "🪤 **Catch** — Set a trap\n"
            "🎒 **Bag** — View your squirrels\n"
            "💰 **Balance** — Check your acorns\n"
            "🐿️ **Profile** — See your stats"
        ),
        inline=False,
    )
    embed.set_footer(text=f"Type {PREFIX}help for all commands")
    await channel.send(embed=embed, view=MenuView())

# ─── COMMANDS ─────────────────────────────────────────────────────────────────

@bot.command(name="help")
async def help_cmd(ctx):
    await do_help(ctx)


@bot.command(name="catch")
async def catch_cmd(ctx):
    await do_catch(ctx)


@bot.command(name="balance", aliases=["bal"])
async def balance_cmd(ctx):
    await do_balance(ctx)


@bot.command(name="bag", aliases=["inventory", "inv"])
async def bag_cmd(ctx):
    await do_bag(ctx)


@bot.command(name="profile")
async def profile_cmd(ctx):
    await do_profile(ctx)


@bot.command(name="exchange", aliases=["ex"])
async def exchange_cmd(ctx, amount: int = 0):
    """Exchange acorns up the currency chain: 100 acorns = 1 silver, 10 silver = 1 emerald, 10 emerald = 1 golden"""
    if amount <= 0:
        await ctx.send(
            "🔄 **Exchange Rates:**\n"
            "• 100 🌰 Acorns → 1 🥈🌰 Silver Acorn\n"
            "• 10 🥈🌰 Silver Acorns → 1 💚🌰 Emerald Acorn\n"
            "• 10 💚🌰 Emerald Acorns → 1 ✨🌰 Golden Acorn\n\n"
            f"Usage: `{PREFIX}exchange <acorns to convert>`"
        )
        return

    user_id = str(ctx.author.id)
    player = await db.get_player(user_id)

    if player["acorns"] < amount:
        await ctx.send(f"❌ You only have **{player['acorns']:,}** 🌰 acorns!")
        return

    silver_gained = amount // 100
    if silver_gained < 1:
        await ctx.send("❌ You need at least **100** 🌰 to exchange!")
        return

    spent = silver_gained * 100
    player["acorns"] -= spent
    player["silver_acorns"] += silver_gained
    await db.update_player(user_id, player)

    await ctx.send(f"🔄 Exchanged **{spent:,}** 🌰 → **{silver_gained:,}** 🥈🌰 Silver Acorns!")


@bot.command(name="exchange_silver", aliases=["exs"])
async def exchange_silver_cmd(ctx, amount: int = 0):
    user_id = str(ctx.author.id)
    player = await db.get_player(user_id)

    if amount <= 0:
        await ctx.send(f"Usage: `{PREFIX}exchange_silver <amount>` (10 🥈🌰 = 1 💚🌰)")
        return
    if player["silver_acorns"] < amount:
        await ctx.send(f"❌ You only have **{player['silver_acorns']:,}** 🥈🌰!")
        return

    emerald_gained = amount // 10
    if emerald_gained < 1:
        await ctx.send("❌ You need at least **10** 🥈🌰 to exchange!")
        return

    spent = emerald_gained * 10
    player["silver_acorns"] -= spent
    player["emerald_acorns"] += emerald_gained
    await db.update_player(user_id, player)

    await ctx.send(f"🔄 Exchanged **{spent:,}** 🥈🌰 → **{emerald_gained:,}** 💚🌰 Emerald Acorns!")


@bot.command(name="exchange_emerald", aliases=["exe"])
async def exchange_emerald_cmd(ctx, amount: int = 0):
    user_id = str(ctx.author.id)
    player = await db.get_player(user_id)

    if amount <= 0:
        await ctx.send(f"Usage: `{PREFIX}exchange_emerald <amount>` (10 💚🌰 = 1 ✨🌰)")
        return
    if player["emerald_acorns"] < amount:
        await ctx.send(f"❌ You only have **{player['emerald_acorns']:,}** 💚🌰!")
        return

    golden_gained = amount // 10
    if golden_gained < 1:
        await ctx.send("❌ You need at least **10** 💚🌰 to exchange!")
        return

    spent = golden_gained * 10
    player["emerald_acorns"] -= spent
    player["golden_acorns"] += golden_gained
    await db.update_player(user_id, player)

    await ctx.send(f"🔄 Exchanged **{spent:,}** 💚🌰 → **{golden_gained:,}** ✨🌰 Golden Acorns!")


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def leaderboard_cmd(ctx):
    await do_leaderboard(ctx)


@bot.command(name="bestiary", aliases=["dex"])
async def bestiary_cmd(ctx):
    await do_bestiary(ctx)


@bot.command(name="sell")
async def sell_cmd(ctx, *, squirrel_name: str = ""):
    if not squirrel_name:
        await ctx.send(f"Usage: `{PREFIX}sell <squirrel name>` — Sell one squirrel for acorns.")
        return

    user_id = str(ctx.author.id)
    player = await db.get_player(user_id)

    # Find matching squirrel (case-insensitive)
    match = None
    for sq in SQUIRRELS:
        if sq[0].lower() == squirrel_name.lower():
            match = sq
            break

    if not match:
        await ctx.send(f"❌ Unknown squirrel: **{squirrel_name}**. Check `{PREFIX}bestiary` for names.")
        return

    sq_name = match[0]
    if sq_name not in player["catches"] or player["catches"][sq_name] < 1:
        await ctx.send(f"❌ You don't have any **{sq_name}** to sell!")
        return

    # Sell value = average of min/max acorn range
    sell_value = (match[3] + match[4]) // 2
    player["catches"][sq_name] -= 1
    if player["catches"][sq_name] == 0:
        del player["catches"][sq_name]
    player["acorns"] += sell_value
    await db.update_player(user_id, player)

    await ctx.send(f"💰 Sold **{sq_name}** for **{sell_value}** 🌰 acorns!")


@bot.command(name="daily")
async def daily_cmd(ctx):
    await do_daily(ctx)


@bot.command(name="shop")
async def shop_cmd(ctx):
    await do_shop(ctx)


@bot.command(name="buy")
async def buy_cmd(ctx, *, item_name: str = ""):
    if not item_name:
        await ctx.send(f"Usage: `{PREFIX}buy <item>` — Use `{PREFIX}shop` to see items.")
        return
    await do_buy(ctx, item_name.lower().replace(" ", "_"))


@bot.command(name="buffs")
async def buffs_cmd(ctx):
    await do_buffs(ctx)


@bot.command(name="donate")
async def donate_cmd(ctx):
    embed = discord.Embed(
        title="💛 Support Squirrel Catcher",
        description=(
            "Thank you for playing Squirrel Catcher!\n\n"
            "Donations help keep the bot running 24/7 and fund new features, "
            "more squirrels, and server costs.\n\n"
            "**[Donate on Ko-fi](https://ko-fi.com/squirrelcatcher)**"
        ),
        color=0xF1C40F,
    )
    embed.set_footer(text="Every acorn counts! 🌰")
    await ctx.send(embed=embed)


# ─── ERROR HANDLING ───────────────────────────────────────────────────────────

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Silently ignore
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument! Try `{PREFIX}help` for usage info.")
    else:
        print(f"Error: {error}")
        await ctx.send("❌ Something went wrong! Try again.")


# ─── RUN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🐿️ Starting Squirrel Catcher Bot...")
    bot.run(BOT_TOKEN)
