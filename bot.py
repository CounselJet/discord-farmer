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
PREFIX = os.getenv("PREFIX", "!sq")

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
    # (name, emoji, rarity, min_acorns, max_acorns, weight_chance, image)
    # ── Common (~78%) ──
    ("Grey Squirrel", "🐿️", "Common", 1, 5, 40, "common_grey.jpg"),
    ("Red Squirrel", "🐿️", "Common", 2, 8, 35, "red_squirrel.jpg"),
    ("Chipmunk", "🐿️", "Common", 1, 4, 38, "chipmunk.jpg"),
    ("Eastern Squirrel", "🌳🐿️", "Common", 2, 6, 32, "eastern_squirrel.jpg"),
    ("Park Squirrel", "🏞️🐿️", "Common", 1, 5, 30, "park_squirrel.jpg"),
    ("Acorn Hoarder", "🌰🐿️", "Common", 3, 7, 28, "acorn_hoarder.jpg"),
    ("Bushy Tail", "🍂🐿️", "Common", 2, 6, 25, "bushy_tail.jpg"),
    ("Tiny Squirrel", "🐾🐿️", "Common", 1, 3, 35, "baby_squirrel.jpg"),
    # ── Uncommon (~20%) ──
    ("Black Squirrel", "🖤🐿️", "Uncommon", 5, 15, 12, "black_squirrel.jpg"),
    ("White Squirrel", "🤍🐿️", "Uncommon", 8, 20, 8, "white_squirrel.jpg"),
    ("Fox Squirrel", "🦊🐿️", "Uncommon", 6, 18, 10, "fox_squirrel.jpg"),
    ("Striped Squirrel", "🦝🐿️", "Uncommon", 7, 16, 9, "striped_squirrel.jpg"),
    ("Pine Squirrel", "🌲🐿️", "Uncommon", 5, 14, 11, "pine_squirrel.jpg"),
    ("Marsh Squirrel", "🌿🐿️", "Uncommon", 6, 15, 8, "marsh_squirrel.jpg"),
    ("Cinnamon Squirrel", "🟤🐿️", "Uncommon", 7, 17, 9, "cinnimon_Squirrel.jpg"),
    # ── Rare (~2%) ──
    ("Flying Squirrel", "🪂🐿️", "Rare", 15, 40, 1.5, "flying_squirrel.jpg"),
    ("Albino Squirrel", "👻🐿️", "Rare", 20, 50, 1.2, "albino_squirrel.jpg"),
    ("Giant Squirrel", "💪🐿️", "Rare", 25, 60, 1.0, "giant_squirrel.jpg"),
    ("Arctic Squirrel", "❄️🐿️", "Rare", 18, 45, 1.3, "artctic_squirrel.jpg"),
    ("Clockwork Squirrel", "⚙️🐿️", "Rare", 22, 55, 0.8, "clockwork_squirrel.jpg"),
    ("Jungle Squirrel", "🌴🐿️", "Rare", 20, 48, 1.0, "jungle_squirrel.jpg"),
    # ── Epic (~0.25%) ──
    ("Crystal Squirrel", "💎🐿️", "Epic", 50, 120, 0.25, "crystal_squirrel.jpg"),
    ("Shadow Squirrel", "🌑🐿️", "Epic", 60, 150, 0.20, "shadow_squirrel.jpg"),
    ("Phoenix Squirrel", "🔥🐿️", "Epic", 55, 130, 0.22, "pheonix_squirrel.jpg"),
    ("Storm Squirrel", "⛈️🐿️", "Epic", 65, 140, 0.18, "storm_squirrel.jpg"),
    # ── Legendary (~0.03%) ──
    ("Golden Squirrel", "👑🐿️", "Legendary", 150, 400, 0.04, "golden_squirrel.jpg"),
    ("Cosmic Squirrel", "🌌🐿️", "Legendary", 200, 500, 0.03, "cosmic_squirrel.jpg"),
    ("Void Squirrel", "🕳️🐿️", "Legendary", 180, 450, 0.035, "void_squirrel.jpg"),
    # ── Mythic (~0.004%) ──
    ("Mythic Nutcracker", "⚡🐿️", "Mythic", 500, 1200, 0.008, "mythic_nutcracker.jpg"),
    ("Celestial Squirrel", "✨🐿️", "Mythic", 600, 1500, 0.005, "celestial_squirrel.jpg"),
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
    # ── Bait — Junk Reduction ──
    "peanut_butter_trap": {"name": "Peanut Butter Trap", "emoji": "🥜", "cost": 150, "currency": "acorns",
                            "description": "-3% junk chance (5 catches)", "type": "consumable", "charges": 5},
    "squirrel_bait": {"name": "Squirrel Bait", "emoji": "🥜", "cost": 500, "currency": "acorns",
                       "description": "-5% junk chance (8 catches)", "type": "consumable", "charges": 8},
    "premium_nuts": {"name": "Premium Nuts", "emoji": "🌰", "cost": 1500, "currency": "acorns",
                      "description": "-8% junk chance (10 catches)", "type": "consumable", "charges": 10},
    "golden_bait": {"name": "Golden Bait", "emoji": "🥇", "cost": 3, "currency": "silver_acorns",
                     "description": "-10% junk chance (12 catches)", "type": "consumable", "charges": 12},
    "honey_trap": {"name": "Honey Trap", "emoji": "🍯", "cost": 8, "currency": "silver_acorns",
                    "description": "-15% junk chance (8 catches)", "type": "consumable", "charges": 8},
    "perfect_bait": {"name": "Perfect Bait", "emoji": "💎", "cost": 3, "currency": "emerald_acorns",
                      "description": "No junk catches (3 charges)", "type": "consumable", "charges": 3},
    # ── Bait — Rarity Attraction ──
    "shiny_acorn_bait": {"name": "Shiny Acorn Bait", "emoji": "✨", "cost": 1200, "currency": "acorns",
                          "description": "+25% Rare+ drop rate (8 catches)", "type": "consumable", "charges": 8},
    "rainbow_bait": {"name": "Rainbow Bait", "emoji": "🌈", "cost": 10000, "currency": "acorns",
                      "description": "+30% Rare+ & -5% junk (8 catches)", "type": "consumable", "charges": 8},
    "rare_scent": {"name": "Rare Scent", "emoji": "✨", "cost": 6000, "currency": "acorns",
                    "description": "+50% Rare+ drop rate (12 catches)", "type": "consumable", "charges": 12},
    "exotic_nectar": {"name": "Exotic Nectar", "emoji": "🌺", "cost": 8000, "currency": "acorns",
                       "description": "+50% Epic+ drop rate (6 catches)", "type": "consumable", "charges": 6},
    "mythic_truffle": {"name": "Mythic Truffle", "emoji": "🍄", "cost": 15, "currency": "silver_acorns",
                        "description": "+200% Mythic drop rate (3 catches)", "type": "consumable", "charges": 3},
    # ── Buffs ──
    "lucky_acorn": {"name": "Lucky Acorn", "emoji": "🍀", "cost": 3000, "currency": "acorns",
                     "description": "2x acorn rewards (20 min)", "type": "timed", "duration_minutes": 20},
    "scholars_cap": {"name": "Scholar's Cap", "emoji": "🎓", "cost": 800, "currency": "acorns",
                      "description": "2x XP (15 catches)", "type": "consumable", "charges": 15},
    "xp_potion": {"name": "XP Potion", "emoji": "🧪", "cost": 4000, "currency": "acorns",
                   "description": "3x XP (20 min)", "type": "timed", "duration_minutes": 20},
    "acorn_storm": {"name": "Acorn Storm", "emoji": "⛈️", "cost": 5, "currency": "silver_acorns",
                     "description": "3x acorn rewards (10 min)", "type": "timed", "duration_minutes": 10},
    "silver_shimmer": {"name": "Silver Shimmer", "emoji": "🪙", "cost": 4000, "currency": "acorns",
                        "description": "10% chance bonus 🥈🌰 (12 catches)", "type": "consumable", "charges": 12},
    "treasure_map": {"name": "Treasure Map", "emoji": "🗺️", "cost": 8000, "currency": "acorns",
                      "description": "+50% sell value (20 min)", "type": "timed", "duration_minutes": 20},
    # ── Helpers ──
    "squirrel_hunter": {"name": "Squirrel Hunter", "emoji": "🏹", "cost": 15000, "currency": "acorns",
                         "description": "Auto-catch every 30 min (24h)", "type": "auto_catch",
                         "interval_minutes": 30, "duration_hours": 24},
    "scout_squirrel": {"name": "Scout Squirrel", "emoji": "🐿️", "cost": 6000, "currency": "acorns",
                        "description": "Auto-catch every 60 min (48h)", "type": "auto_catch",
                        "interval_minutes": 60, "duration_hours": 48},
    "elite_hunter": {"name": "Elite Hunter", "emoji": "⚔️", "cost": 15, "currency": "silver_acorns",
                      "description": "Auto-catch every 15 min (24h)", "type": "auto_catch",
                      "interval_minutes": 15, "duration_hours": 24},
    "master_hunter": {"name": "Master Hunter", "emoji": "🦅", "cost": 25, "currency": "silver_acorns",
                       "description": "Auto-catch every 10 min (12h)", "type": "auto_catch",
                       "interval_minutes": 10, "duration_hours": 12},
}

UPGRADE_TIERS = {
    "trap_tier": {"name": "Trap Speed", "max": 3,
                   "tiers": [{"cost": 2000, "label": "3s cooldown"}, {"cost": 10000, "label": "2.5s cooldown"}, {"cost": 40000, "label": "2s cooldown"}]},
    "junk_resist_tier": {"name": "Junk Resistance", "max": 3,
                          "tiers": [{"cost": 3000, "label": "-3% junk"}, {"cost": 15000, "label": "-5% junk"}, {"cost": 60000, "label": "-8% junk"}]},
    "acorn_magnet_tier": {"name": "Acorn Magnet", "max": 3,
                           "tiers": [{"cost": 5000, "label": "+5% acorns"}, {"cost": 25000, "label": "+10% acorns"}, {"cost": 80000, "label": "+15% acorns"}]},
}

TRAP_COOLDOWNS = [3.5, 3, 2.5, 2]  # index = trap_tier
JUNK_RESIST_BONUSES = [0, 3, 5, 8]  # index = junk_resist_tier
ACORN_MAGNET_BONUSES = [0, 5, 10, 15]  # index = acorn_magnet_tier

# ─── COOLDOWNS ────────────────────────────────────────────────────────────────

CATCH_COOLDOWN = 3.5  # base seconds between catches
cooldowns: dict[int, datetime] = {}

# Track which menu page an interaction came from (Interaction uses __slots__)
_interaction_pages: dict[int, str] = {}

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
               bait_junk_reduction: int = 0,
               rare_bonus: int = 0, epic_bonus: int = 0, mythic_bonus: int = 0) -> tuple:
    """Returns either a squirrel tuple or a junk tuple.
    junk_resist_tier: permanent junk reduction tier (0-3)
    bait_junk_reduction: temporary junk % reduction from bait buffs
    rare_bonus: % boost to Rare+ squirrels
    epic_bonus: % boost to Epic+ squirrels
    mythic_bonus: % boost to Mythic squirrels
    """
    # 30% chance of junk, decreasing slightly with level
    junk_chance = max(5, 30 - player_level - JUNK_RESIST_BONUSES[junk_resist_tier] - bait_junk_reduction)
    if random.randint(1, 100) <= junk_chance:
        return ("junk", random.choice(JUNK_CATCHES))

    # Weighted random squirrel selection
    # Higher level = slightly better luck
    level_bonus = min(player_level * 0.5, 10)  # up to +10% at high levels
    weights = []
    for sq in SQUIRRELS:
        w = sq[5]
        rarity = sq[2]
        if rarity == "Rare":
            w *= (1 + (level_bonus + rare_bonus) / 100)
        elif rarity == "Epic":
            w *= (1 + (level_bonus + rare_bonus + epic_bonus) / 100)
        elif rarity == "Legendary":
            w *= (1 + (level_bonus + rare_bonus + epic_bonus) / 100)
        elif rarity == "Mythic":
            w *= (1 + (level_bonus + rare_bonus + epic_bonus + mythic_bonus) / 100)
        weights.append(w)

    chosen = random.choices(SQUIRRELS, weights=weights, k=1)[0]
    acorns = random.randint(chosen[3], chosen[4])

    # Level bonus to acorns
    acorns = int(acorns * (1 + player_level * 0.02))

    return ("squirrel", chosen, acorns)

# ─── MENU PAGES ──────────────────────────────────────────────────────────────

MENU_PAGES = {
    "play": {"label": "Play", "emoji": "🎮"},
    "shop": {"label": "Shop & Buffs", "emoji": "🛒"},
    "info": {"label": "Info", "emoji": "📋"},
}


async def get_page_embed(page, user):
    """Get the navigation embed shown when switching to a menu page."""
    if page == "play":
        return discord.Embed(
            title="🐿️ Squirrel Catcher",
            description=(
                "Set traps, catch squirrels, and become the ultimate wrangler!\n"
                "Use the buttons below to play, or the dropdown to navigate."
            ),
            color=0x8B4513,
        )
    elif page == "shop":
        player = await db.get_player(str(user.id))
        embed = discord.Embed(
            title="🛒 Shop & Buffs",
            description="Spend your acorns on buffs and permanent upgrades!",
            color=0xE67E22,
        )
        embed.add_field(
            name="Your Balance",
            value=f"🌰 {player.get('acorns', 0):,} | 🥈🌰 {player.get('silver_acorns', 0):,} | 💚🌰 {player.get('emerald_acorns', 0):,}",
            inline=False,
        )
        return embed
    elif page == "info":
        return discord.Embed(
            title="📋 Information",
            description="Check your daily bonus, explore the bestiary, view leaderboards, and more!",
            color=0x3498DB,
        )
    return discord.Embed(title="🐿️ Squirrel Catcher", color=0x8B4513)


# ─── MENU COMPONENTS ────────────────────────────────────────────────────────

class MenuButton(discord.ui.Button):
    """A button that triggers a game action and sends a new message."""
    def __init__(self, *, action, **kwargs):
        super().__init__(**kwargs)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        # Carry the current page context so response messages keep the same menu
        _interaction_pages[interaction.id] = self.view.current_page
        handlers = {
            "catch": do_catch, "bag": do_bag, "balance": do_balance,
            "profile": do_profile, "shop": do_shop, "buffs": do_buffs,
            "shop_items": do_shop_items, "shop_upgrades": do_shop_upgrades,
            "daily": do_daily, "bestiary": do_bestiary,
            "leaderboard": do_leaderboard, "exchange": do_exchange_view,
            "help": do_help,
        }
        handler = handlers.get(self.action)
        if handler:
            await handler(interaction)



class PageSelect(discord.ui.Select):
    """Dropdown to switch between menu pages by editing the message."""
    def __init__(self, current_page, row=0):
        options = [
            discord.SelectOption(
                label=info["label"], value=key, emoji=info["emoji"],
                default=(key == current_page),
            )
            for key, info in MENU_PAGES.items()
        ]
        super().__init__(
            options=options, custom_id=f"{current_page}:select",
            placeholder="Navigate...", row=row,
        )
        self.current_page = current_page

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == self.current_page:
            await interaction.response.defer()
            return
        embed = await get_page_embed(selected, interaction.user)
        view = MenuView(page=selected)
        await interaction.response.edit_message(embed=embed, view=view)


class MenuView(discord.ui.View):
    """Dynamic menu view that shows different buttons based on the current page."""
    def __init__(self, page="play"):
        super().__init__(timeout=None)
        self.current_page = page

        # Row 0: Page selector (always on top)
        self.add_item(PageSelect(current_page=page, row=0))

        # Row 1: Page-specific action buttons
        if page == "play":
            self.add_item(MenuButton(label="Catch!", emoji="🪤", style=discord.ButtonStyle.green,
                                     action="catch", custom_id="play:catch", row=1))
            self.add_item(MenuButton(label="Bag", emoji="🎒", style=discord.ButtonStyle.primary,
                                     action="bag", custom_id="play:bag", row=1))
            self.add_item(MenuButton(label="Balance", emoji="💰", style=discord.ButtonStyle.primary,
                                     action="balance", custom_id="play:balance", row=1))
            self.add_item(MenuButton(label="Profile", emoji="🐿️", style=discord.ButtonStyle.primary,
                                     action="profile", custom_id="play:profile", row=1))
            self.add_item(MenuButton(label="Exchange", emoji="🔄", style=discord.ButtonStyle.primary,
                                     action="exchange", custom_id="play:exchange", row=2))
            self.add_item(discord.ui.Button(label="Donate", style=discord.ButtonStyle.link,
                                            emoji="💛", url="https://ko-fi.com/squirrelcatcher", row=2))
        elif page == "shop":
            self.add_item(MenuButton(label="Items", emoji="🛒", style=discord.ButtonStyle.green,
                                     action="shop_items", custom_id="shop:items", row=1))
            self.add_item(MenuButton(label="Upgrades", emoji="🪤", style=discord.ButtonStyle.green,
                                     action="shop_upgrades", custom_id="shop:upgrades_menu", row=1))
            self.add_item(MenuButton(label="Active Buffs", emoji="⚡", style=discord.ButtonStyle.primary,
                                     action="buffs", custom_id="shop:buffs", row=1))
        elif page == "info":
            self.add_item(MenuButton(label="Daily", emoji="🎁", style=discord.ButtonStyle.green,
                                     action="daily", custom_id="info:daily", row=1))
            self.add_item(MenuButton(label="Bestiary", emoji="📖", style=discord.ButtonStyle.primary,
                                     action="bestiary", custom_id="info:bestiary", row=1))
            self.add_item(MenuButton(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.primary,
                                     action="leaderboard", custom_id="info:leaderboard", row=1))
            self.add_item(MenuButton(label="Help", emoji="❓", style=discord.ButtonStyle.primary,
                                     action="help", custom_id="info:help", row=1))



# ─── SHOP VIEWS ──────────────────────────────────────────────────────────────

# Shop item categories
_SHOP_CATEGORIES = {
    "bait":    {"label": "Bait",    "emoji": "🥜", "keys": [
        "peanut_butter_trap", "squirrel_bait", "premium_nuts", "golden_bait", "honey_trap", "perfect_bait",
        "shiny_acorn_bait", "rainbow_bait", "rare_scent", "exotic_nectar", "mythic_truffle",
    ]},
    "buffs":   {"label": "Buffs",   "emoji": "🍀", "keys": [
        "lucky_acorn", "scholars_cap", "xp_potion", "acorn_storm", "silver_shimmer", "treasure_map",
    ]},
    "helpers": {"label": "Helpers", "emoji": "🏹", "keys": [
        "scout_squirrel", "squirrel_hunter", "elite_hunter", "master_hunter",
    ]},
}
_SHOP_CONSUMABLE_KEYS = [k for k, v in SHOP_ITEMS.items() if v["type"] != "upgrade"]


def _item_category(item_key):
    """Return the shop category for a given item key, or 'bait' as default."""
    for cat_key, cat in _SHOP_CATEGORIES.items():
        if item_key in cat["keys"]:
            return cat_key
    return "bait"


class BuyButton(discord.ui.Button):
    """A button that purchases a shop item when clicked."""
    def __init__(self, item_key, *, player=None, row=0):
        item = SHOP_ITEMS.get(item_key) or {}
        label = item.get("name", item_key)
        emoji = item.get("emoji")
        currency = item.get("currency", "acorns")
        cost = item.get("cost", 0)
        currency_emoji = CURRENCIES.get(currency, "🌰")
        cost_str = f" ({cost:,}{currency_emoji})"
        can_afford = (player or {}).get(currency, 0) >= cost if player else True
        super().__init__(
            label=f"{label}{cost_str}",
            emoji=emoji,
            style=discord.ButtonStyle.green,
            disabled=not can_afford,
            custom_id=f"buy:{item_key}",
            row=row,
        )
        self.item_key = item_key

    async def callback(self, interaction: discord.Interaction):
        await do_buy(interaction, self.item_key)


class ShopItemsView(discord.ui.View):
    """Category-tabbed view of purchasable shop items."""
    def __init__(self, player=None, category="bait"):
        super().__init__(timeout=None)
        self.category = category

        # Row 0: Category tabs (current one disabled)
        for cat_key, cat in _SHOP_CATEGORIES.items():
            self.add_item(ShopCategoryButton(
                cat_key=cat_key, label=cat["label"], emoji=cat["emoji"],
                is_current=(cat_key == category), row=0,
            ))

        # Rows 1-3: Buy buttons for items in selected category (4 per row)
        cat_keys = _SHOP_CATEGORIES[category]["keys"]
        for i, key in enumerate(cat_keys):
            self.add_item(BuyButton(key, player=player, row=1 + i // 4))

        # Row 4: Back button
        self.add_item(BackToShopMenuButton(row=4))


class ShopCategoryButton(discord.ui.Button):
    """Tab button to switch shop item categories."""
    def __init__(self, *, cat_key, label, emoji, is_current, row):
        super().__init__(
            label=label, emoji=emoji,
            style=discord.ButtonStyle.primary if is_current else discord.ButtonStyle.secondary,
            disabled=is_current,
            custom_id=f"shop_cat:{cat_key}",
            row=row,
        )
        self.cat_key = cat_key

    async def callback(self, interaction: discord.Interaction):
        player = await db.get_player(str(interaction.user.id))
        embed = _build_shop_embed(player, category=self.cat_key)
        await interaction.response.edit_message(embed=embed, view=ShopItemsView(player=player, category=self.cat_key))



class BackToShopMenuButton(discord.ui.Button):
    """Back button that returns to the main shop menu page."""
    def __init__(self, row=4):
        super().__init__(label="Back", emoji="⬅", style=discord.ButtonStyle.secondary,
                         custom_id="shop:back_menu", row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = await get_page_embed("shop", interaction.user)
        await interaction.response.edit_message(embed=embed, view=MenuView(page="shop"))


class ShopUpgradeView(discord.ui.View):
    """View for purchasing permanent upgrades."""
    def __init__(self, player=None):
        super().__init__(timeout=None)
        # Row 0: Upgrade buy buttons
        for key, upgrade in UPGRADE_TIERS.items():
            current_tier = (player or {}).get(key, 0)
            acorns = (player or {}).get("acorns", 0)
            if current_tier >= upgrade["max"]:
                label = f"{upgrade['name']} (MAX)"
                disabled = True
                cost_str = ""
            else:
                tier = upgrade["tiers"][current_tier]
                label = f"{upgrade['name']}"
                cost_str = f" ({tier['cost']:,}🌰)"
                disabled = acorns < tier["cost"]
            self.add_item(UpgradeBuyButton(
                upgrade_key=key, label=f"{label}{cost_str}",
                disabled=disabled, row=0,
            ))

        # Row 4: Back to shop menu
        self.add_item(BackToShopMenuButton2(row=4))


class UpgradeBuyButton(discord.ui.Button):
    """Button to purchase a specific upgrade tier."""
    def __init__(self, upgrade_key, label, disabled, row):
        super().__init__(
            label=label, emoji="🪤",
            style=discord.ButtonStyle.green,
            disabled=disabled,
            custom_id=f"buy_upgrade:{upgrade_key}",
            row=row,
        )
        self.upgrade_key = upgrade_key

    async def callback(self, interaction: discord.Interaction):
        await do_buy(interaction, self.upgrade_key)


class BackToShopMenuButton2(discord.ui.Button):
    """Back button on upgrade view that returns to the main shop menu."""
    def __init__(self, row=4):
        super().__init__(label="Back", emoji="⬅",
                         style=discord.ButtonStyle.secondary,
                         custom_id="shop:back_from_upgrades", row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = await get_page_embed("shop", interaction.user)
        await interaction.response.edit_message(embed=embed, view=MenuView(page="shop"))


def _build_shop_embed(player, category=None):
    """Build the shop embed showing items and balance."""
    if category and category in _SHOP_CATEGORIES:
        cat = _SHOP_CATEGORIES[category]
        embed = discord.Embed(title=f"🛒 Squirrel Shop — {cat['emoji']} {cat['label']}", color=0xE67E22)
        keys = cat["keys"]
    else:
        embed = discord.Embed(title="🛒 Squirrel Shop", color=0xE67E22)
        keys = _SHOP_CONSUMABLE_KEYS
    item_lines = []
    for key in keys:
        item = SHOP_ITEMS[key]
        currency_emoji = CURRENCIES.get(item["currency"], "🌰")
        item_lines.append(f"{item['emoji']} **{item['name']}** — {item['cost']:,} {currency_emoji}\n  _{item['description']}_")
    embed.add_field(name="Items", value="\n".join(item_lines), inline=False)
    embed.add_field(
        name="Your Balance",
        value=f"🌰 {player.get('acorns', 0):,} | 🥈🌰 {player.get('silver_acorns', 0):,} | 💚🌰 {player.get('emerald_acorns', 0):,}",
        inline=False,
    )
    return embed


def _build_upgrades_embed(player):
    """Build the embed for the permanent upgrades sub-menu."""
    embed = discord.Embed(title="🪤 Permanent Upgrades", color=0xE67E22)
    for key, upgrade in UPGRADE_TIERS.items():
        current_tier = player.get(key, 0)
        tier_display = []
        for i, tier in enumerate(upgrade["tiers"]):
            if i < current_tier:
                tier_display.append(f"~~Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)~~ ✅")
            elif i == current_tier:
                tier_display.append(f"**Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)** ← Next")
            else:
                tier_display.append(f"Tier {i+1}: {tier['label']} ({tier['cost']:,} 🌰)")
        if current_tier >= upgrade["max"]:
            status = f"**{upgrade['name']}** — MAX ✅"
        else:
            status = f"**{upgrade['name']}**\n" + "\n".join(tier_display)
        embed.add_field(name="\u200b", value=status, inline=False)
    embed.add_field(
        name="Your Balance",
        value=f"🌰 {player.get('acorns', 0):,}",
        inline=False,
    )
    return embed


# ─── EXCHANGE VIEW ────────────────────────────────────────────────────────────

# (from_currency, to_currency, cost_per_unit, gain_per_unit, emoji_from, emoji_to)
_EXCHANGE_TIERS = [
    ("acorns", "silver_acorns", 100, 1, "🌰", "🥈🌰"),
    ("silver_acorns", "emerald_acorns", 10, 1, "🥈🌰", "💚🌰"),
    ("emerald_acorns", "golden_acorns", 10, 1, "💚🌰", "✨🌰"),
]


class ExchangeView(discord.ui.View):
    """View with buttons to exchange currencies (1, 5, 10, All per tier)."""
    def __init__(self, player):
        super().__init__(timeout=None)
        for i, (from_cur, to_cur, cost, gain, emoji_from, emoji_to) in enumerate(_EXCHANGE_TIERS):
            available = player.get(from_cur, 0)
            max_units = available // cost
            for amount in [1, 5, 10, "Max"]:
                if amount == "Max":
                    units = max_units
                    label = f"Max {emoji_from}→{emoji_to}"
                    cid = f"exchange:{from_cur}_to_{to_cur}_max"
                else:
                    units = amount
                    label = f"{amount} {emoji_to}"
                    cid = f"exchange:{from_cur}_to_{to_cur}_{amount}"
                self.add_item(ExchangeButton(
                    from_currency=from_cur, to_currency=to_cur,
                    cost_per_unit=cost, gain_per_unit=gain,
                    emoji_from=emoji_from, emoji_to=emoji_to,
                    units=units, label=label, custom_id=cid,
                    disabled=(max_units < (units if amount != "Max" else 1)),
                    row=i,
                ))
        # Row 4: Back
        self.add_item(BackToPlayMenuButton(row=4))


class ExchangeButton(discord.ui.Button):
    """Button that exchanges a specific number of currency units."""
    def __init__(self, *, from_currency, to_currency, cost_per_unit, gain_per_unit,
                 emoji_from, emoji_to, units, label, custom_id, disabled, row):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.green,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
        )
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.cost_per_unit = cost_per_unit
        self.gain_per_unit = gain_per_unit
        self.units = units
        self.emoji_from = emoji_from
        self.emoji_to = emoji_to

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        player = await db.get_player(user_id)

        available = player.get(self.from_currency, 0)
        max_units = available // self.cost_per_unit
        # For "All", self.units was set at view creation; recalculate from live data
        units = min(self.units, max_units) if self.units > 0 else max_units

        if units < 1:
            await interaction.response.send_message(
                f"❌ You need at least **{self.cost_per_unit}** {self.emoji_from} to exchange!",
                ephemeral=True,
            )
            return

        spent = units * self.cost_per_unit
        gained = units * self.gain_per_unit

        player[self.from_currency] -= spent
        player[self.to_currency] = player.get(self.to_currency, 0) + gained
        await db.update_player(user_id, player)

        embed = discord.Embed(
            title="🔄 Exchange Complete!",
            description=f"**{spent:,}** {self.emoji_from} → **{gained:,}** {self.emoji_to}",
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Refresh the exchange view with updated balances
        refreshed_player = await db.get_player(user_id)
        exchange_embed = _build_exchange_embed(refreshed_player)
        await interaction.message.edit(embed=exchange_embed, view=ExchangeView(refreshed_player))


class BackToPlayMenuButton(discord.ui.Button):
    """Back button that returns to the play menu page."""
    def __init__(self, row=4):
        super().__init__(label="Back", emoji="⬅", style=discord.ButtonStyle.secondary,
                         custom_id="exchange:back", row=row)

    async def callback(self, interaction: discord.Interaction):
        embed = await get_page_embed("play", interaction.user)
        await interaction.response.edit_message(embed=embed, view=MenuView(page="play"))


def _build_exchange_embed(player):
    """Build the exchange embed showing rates and balances."""
    embed = discord.Embed(title="🔄 Currency Exchange", color=0x3498DB)
    embed.description = (
        "Exchange your currencies! Choose an amount to convert.\n\n"
        "**Rates:**\n"
        "• 100 🌰 → 1 🥈🌰 Silver Acorn\n"
        "• 10 🥈🌰 → 1 💚🌰 Emerald Acorn\n"
        "• 10 💚🌰 → 1 ✨🌰 Golden Acorn"
    )
    embed.add_field(
        name="Your Balance",
        value=(
            f"🌰 {player.get('acorns', 0):,} | "
            f"🥈🌰 {player.get('silver_acorns', 0):,} | "
            f"💚🌰 {player.get('emerald_acorns', 0):,} | "
            f"✨🌰 {player.get('golden_acorns', 0):,}"
        ),
        inline=False,
    )
    return embed


async def do_exchange_view(ctx_or_interaction):
    """Show the exchange view with clickable exchange buttons."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    embed = _build_exchange_embed(player)
    view = ExchangeView(player)
    if is_interaction:
        await ctx_or_interaction.response.edit_message(embed=embed, view=view)
    else:
        await ctx_or_interaction.send(embed=embed, view=view)


async def _send(ctx_or_interaction, embed, view=None, ephemeral=False):
    """Send an embed from either a command context or interaction."""
    if view is None:
        iid = getattr(ctx_or_interaction, 'id', None)
        page = _interaction_pages.pop(iid, 'play') if iid else 'play'
        view = MenuView(page=page)
    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx_or_interaction.send(embed=embed, view=view)


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
    rare_bonus = 0
    epic_bonus = 0
    mythic_bonus = 0
    xp_multiplier = 1
    acorn_multiplier = 1
    has_silver_shimmer = False
    has_treasure_map = False
    charge_buff_ids = []  # (buff_id, buff_type) for charge-based buffs to consume

    for buff in active_buffs:
        bt = buff["buff_type"]
        bid = buff["id"]
        if bt == "peanut_butter_trap":
            bait_junk_reduction = max(bait_junk_reduction, 3)
            charge_buff_ids.append(bid)
        elif bt == "squirrel_bait":
            bait_junk_reduction = max(bait_junk_reduction, 5)
            charge_buff_ids.append(bid)
        elif bt == "premium_nuts":
            bait_junk_reduction = max(bait_junk_reduction, 8)
            charge_buff_ids.append(bid)
        elif bt == "golden_bait":
            bait_junk_reduction = max(bait_junk_reduction, 10)
            charge_buff_ids.append(bid)
        elif bt == "honey_trap":
            bait_junk_reduction = max(bait_junk_reduction, 15)
            charge_buff_ids.append(bid)
        elif bt == "perfect_bait":
            bait_junk_reduction = 100
            charge_buff_ids.append(bid)
        elif bt == "shiny_acorn_bait":
            rare_bonus = max(rare_bonus, 25)
            charge_buff_ids.append(bid)
        elif bt == "rainbow_bait":
            rare_bonus = max(rare_bonus, 30)
            bait_junk_reduction = max(bait_junk_reduction, 5)
            charge_buff_ids.append(bid)
        elif bt == "rare_scent":
            rare_bonus = max(rare_bonus, 50)
            charge_buff_ids.append(bid)
        elif bt == "exotic_nectar":
            epic_bonus = max(epic_bonus, 50)
            charge_buff_ids.append(bid)
        elif bt == "mythic_truffle":
            mythic_bonus = max(mythic_bonus, 200)
            charge_buff_ids.append(bid)
        elif bt == "lucky_acorn":
            acorn_multiplier = max(acorn_multiplier, 2)
        elif bt == "scholars_cap":
            xp_multiplier = max(xp_multiplier, 2)
            charge_buff_ids.append(bid)
        elif bt == "xp_potion":
            xp_multiplier = max(xp_multiplier, 3)
        elif bt == "acorn_storm":
            acorn_multiplier = max(acorn_multiplier, 3)
        elif bt == "silver_shimmer":
            has_silver_shimmer = True
            charge_buff_ids.append(bid)
        elif bt == "treasure_map":
            has_treasure_map = True

    # Suspense message
    if is_interaction:
        await ctx_or_interaction.response.send_message("🪤 Setting your trap in the forest...")
        msg = await ctx_or_interaction.original_response()
    else:
        msg = await ctx_or_interaction.send("🪤 Setting your trap in the forest...")
    await asyncio.sleep(1.5)

    result = roll_catch(player["level"], player.get("junk_resist_tier", 0),
                        bait_junk_reduction, rare_bonus, epic_bonus, mythic_bonus)

    # Consume charge-based buffs that were used
    for bid in charge_buff_ids:
        await db.consume_buff_charge(bid)

    if result[0] == "junk":
        _, (junk_name, junk_emoji, junk_acorns) = result
        player["junk_catches"] += 1
        player["acorns"] += junk_acorns
        player["xp"] += 1 * xp_multiplier

        embed = discord.Embed(
            title=f"{junk_emoji} You caught... {junk_name}!",
            description=f"Better luck next time!" + (f"\nBut you found **{junk_acorns}** 🌰!" if junk_acorns > 0 else ""),
            color=0x95A5A6,
        )
    else:
        _, squirrel, acorns = result
        sq_name, sq_emoji, sq_rarity, _, _, _, sq_image = squirrel

        # Apply acorn bonuses
        magnet_bonus = ACORN_MAGNET_BONUSES[player.get("acorn_magnet_tier", 0)]
        acorns = int(acorns * (1 + magnet_bonus / 100))
        acorns *= acorn_multiplier

        player["acorns"] += acorns
        player["total_catches"] += 1
        player["catches"][sq_name] = player["catches"].get(sq_name, 0) + 1

        xp_gain = {"Common": 5, "Uncommon": 10, "Rare": 20, "Epic": 40, "Legendary": 80, "Mythic": 200}
        player["xp"] += xp_gain.get(sq_rarity, 5) * xp_multiplier

        embed = discord.Embed(
            title=f"{sq_emoji} {user.display_name} caught a {sq_name}!",
            description=f"**Rarity:** {sq_rarity}\n**Reward:** {acorns} 🌰",
            color=RARITY_COLORS.get(sq_rarity, 0x808080),
        )

        image_path = f"assets/{sq_image}"
        file = discord.File(image_path, filename=sq_image)
        embed.set_thumbnail(url=f"attachment://{sq_image}")

        bonus_notes = []
        if acorn_multiplier > 1:
            bonus_notes.append(f"{acorn_multiplier}x Acorns!")
        if xp_multiplier > 1:
            bonus_notes.append(f"{xp_multiplier}x XP!")
        if bonus_notes:
            embed.description += f" ({' | '.join(bonus_notes)})"

        # Silver shimmer: 10% chance for bonus silver acorn
        if has_silver_shimmer and random.random() < 0.10:
            player["silver_acorns"] = player.get("silver_acorns", 0) + 1
            embed.description += "\n🪙 **Silver Shimmer!** +1 🥈🌰"

        if sq_rarity in ("Epic", "Legendary", "Mythic"):
            embed.set_footer(text=f"🎉 Wow! A {sq_rarity} catch!")

    leveled = check_level_up(player)
    if leveled:
        embed.add_field(name="🎉 LEVEL UP!", value=f"You are now **Level {player['level']}**!", inline=False)

    await db.update_player(user_id, player)
    iid = getattr(ctx_or_interaction, 'id', None)
    page = _interaction_pages.pop(iid, 'play') if iid else 'play'
    if result[0] == "squirrel":
        await msg.edit(content=None, embed=embed, view=MenuView(page=page), attachments=[file])
    else:
        await msg.edit(content=None, embed=embed, view=MenuView(page=page))


async def do_bag(ctx_or_interaction):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    user_id = str(user.id)
    player = await db.get_player(user_id)
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

    # Show active buffs in bag
    active_buffs = await db.get_active_buffs(user_id)
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
            embed.add_field(name="⚡ Active Buffs", value="\n".join(buff_lines), inline=False)

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
    now = datetime.now(timezone.utc)

    if last_daily:
        last = datetime.fromisoformat(last_daily)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
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
        name, emoji, rarity, _, _, _, _ = sq
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
    """Show the shop embed with the main shop menu (Items / Upgrades / Active Buffs)."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    embed = _build_shop_embed(player)
    await _send(ctx_or_interaction, embed, view=MenuView(page="shop"))


async def do_shop_items(ctx_or_interaction):
    """Show the paginated shop items view with buy buttons."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    embed = _build_shop_embed(player, category="bait")
    view = ShopItemsView(player=player, category="bait")
    if is_interaction:
        await ctx_or_interaction.response.edit_message(embed=embed, view=view)
    else:
        await ctx_or_interaction.send(embed=embed, view=view)


async def do_shop_upgrades(ctx_or_interaction):
    """Show the permanent upgrades view with buy buttons."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    user = ctx_or_interaction.user if is_interaction else ctx_or_interaction.author
    player = await db.get_player(str(user.id))

    embed = _build_upgrades_embed(player)
    view = ShopUpgradeView(player)
    if is_interaction:
        await ctx_or_interaction.response.edit_message(embed=embed, view=view)
    else:
        await ctx_or_interaction.send(embed=embed, view=view)


async def do_buy(ctx_or_interaction, item_key: str):
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)
    # Detect if this was triggered by a button click (component interaction)
    from_button = is_interaction and ctx_or_interaction.type == discord.InteractionType.component
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
        if from_button:
            await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            # Refresh the upgrades view on the original message
            refreshed_player = await db.get_player(user_id)
            upgrade_embed = _build_upgrades_embed(refreshed_player)
            await ctx_or_interaction.message.edit(embed=upgrade_embed, view=ShopUpgradeView(refreshed_player))
        else:
            await _send(ctx_or_interaction, embed)
        return

    # Check shop items
    if item_key not in SHOP_ITEMS:
        msg = f"❌ Unknown item: **{item_key}**. Use `{PREFIX} shop` to see available items."
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
    if from_button:
        await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
        # Refresh the shop view on the original message with updated balance
        refreshed_player = await db.get_player(user_id)
        # Determine which category the purchased item belongs to
        cat = _item_category(item_key)
        shop_embed = _build_shop_embed(refreshed_player, category=cat)
        await ctx_or_interaction.message.edit(embed=shop_embed, view=ShopItemsView(player=refreshed_player, category=cat))
    else:
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
        embed.add_field(name="Active Buffs", value=f"No active buffs. Visit `{PREFIX} shop` to buy some!", inline=False)

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
        embed.add_field(name="Permanent Upgrades", value=f"None yet. Visit `{PREFIX} shop`!", inline=False)

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

        result = roll_catch(player["level"], player.get("junk_resist_tier", 0), 0, 0, 0, 0)

        if result[0] == "junk":
            _, (junk_name, junk_emoji, junk_acorns) = result
            player["junk_catches"] += 1
            player["acorns"] += junk_acorns
            player["xp"] += 1
            embed = discord.Embed(
                title=f"{junk_emoji} Auto-Catch: {junk_name}",
                description=f"<@{user_id}>" + (f" +{junk_acorns} 🌰" if junk_acorns else ""),
                color=0x808080,
            )
        else:
            _, squirrel, acorns = result
            sq_name, sq_emoji, sq_rarity, _, _, _, _ = squirrel
            magnet_bonus = ACORN_MAGNET_BONUSES[player.get("acorn_magnet_tier", 0)]
            acorns = int(acorns * (1 + magnet_bonus / 100))
            player["acorns"] += acorns
            player["total_catches"] += 1
            player["catches"][sq_name] = player["catches"].get(sq_name, 0) + 1
            xp_gain = {"Common": 5, "Uncommon": 10, "Rare": 20, "Epic": 40, "Legendary": 80, "Mythic": 200}
            player["xp"] += xp_gain.get(sq_rarity, 5)
            embed = discord.Embed(
                title=f"{sq_emoji} Auto-Catch: {sq_name}!",
                description=f"<@{user_id}> {sq_rarity} — +{acorns} 🌰",
                color=RARITY_COLORS.get(sq_rarity, 0x808080),
            )

        leveled = check_level_up(player)
        if leveled:
            embed.add_field(name="🎉 LEVEL UP!", value=f"Now **Level {player['level']}**!", inline=False)
        embed.set_footer(text=item.get("name", "Auto-Catch"))

        await db.update_player(user_id, player)
        await db.update_buff_last_triggered(buff["id"])

        try:
            channel = bot.get_channel(int(buff["channel_id"]))
            if channel:
                await channel.send(embed=embed)
        except Exception:
            pass

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
                WHERE buff_type IN ('squirrel_hunter', 'elite_hunter', 'scout_squirrel', 'master_hunter')
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
    # Register persistent views for each page
    for page in MENU_PAGES:
        bot.add_view(MenuView(page=page))
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
            f"Use the **buttons** below or type commands with `{PREFIX}`.\n"
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

    # Check for treasure map buff (+50% sell value)
    active_buffs = await db.get_active_buffs(user_id)
    has_treasure_map = any(b["buff_type"] == "treasure_map" for b in active_buffs)
    if has_treasure_map:
        sell_value = int(sell_value * 1.5)

    player["catches"][sq_name] -= 1
    if player["catches"][sq_name] == 0:
        del player["catches"][sq_name]
    player["acorns"] += sell_value
    await db.update_player(user_id, player)

    bonus = " (🗺️ +50% Treasure Map!)" if has_treasure_map else ""
    await ctx.send(f"💰 Sold **{sq_name}** for **{sell_value}** 🌰 acorns!{bonus}")


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
