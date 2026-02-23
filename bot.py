"""
🐿️ Squirrel Catcher - A Discord Bot
Catch squirrels, earn acorns, and become the ultimate squirrel wrangler!
"""

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random
import asyncio
from datetime import datetime, timedelta

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

# ─── COOLDOWNS ────────────────────────────────────────────────────────────────

CATCH_COOLDOWN = 10  # seconds between catches
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

def roll_catch(player_level: int) -> tuple:
    """Returns either a squirrel tuple or a junk tuple."""
    # 30% chance of junk, decreasing slightly with level
    junk_chance = max(15, 30 - player_level)
    if random.randint(1, 100) <= junk_chance:
        return ("junk", random.choice(JUNK_CATCHES))

    # Weighted random squirrel selection
    # Higher level = slightly better luck
    level_bonus = min(player_level * 0.5, 10)
    weights = []
    for sq in SQUIRRELS:
        w = sq[5]
        # Boost rare+ squirrels slightly based on level
        if sq[2] in ("Rare", "Epic", "Legendary", "Mythic"):
            w *= (1 + level_bonus / 100)
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
        if choice == "daily":
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

    # Cooldown check
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

    cooldowns[user_id] = now + timedelta(seconds=CATCH_COOLDOWN)
    player = await db.get_player(user_id)

    # Suspense message
    if is_interaction:
        await ctx_or_interaction.response.send_message("🪤 Setting your trap in the forest...")
        msg = await ctx_or_interaction.original_response()
    else:
        msg = await ctx_or_interaction.send("🪤 Setting your trap in the forest...")
    await asyncio.sleep(1.5)

    result = roll_catch(player["level"])

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


# ─── BOT EVENTS ───────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    await db.init_db(DATABASE_URL)
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
