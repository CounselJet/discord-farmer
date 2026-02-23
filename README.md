# Squirrel Catcher

A Discord bot game where you catch squirrels, earn acorns, level up, and compete with friends.

[Add to your server](https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands)

## Features

- **14 squirrel species** across 6 rarities (Common to Mythic)
- **Leveling system** — gain XP from catches, unlock better drop rates at higher levels
- **Multi-tier currency** — Acorns, Silver Acorns, Emerald Acorns, Golden Acorns
- **Bestiary** — track discoveries of all species
- **Leaderboard** — compete with friends
- **Daily bonus** — scales with your level
- **Persistent data** — PostgreSQL database

## Commands

All commands use the `!sq` prefix.

| Command | Aliases | Description |
|---------|---------|-------------|
| `!sq catch` | | Set a trap and catch a squirrel (or junk) |
| `!sq bag` | `inv`, `inventory` | View your caught squirrels |
| `!sq balance` | `bal` | Check your acorn balances |
| `!sq profile` | | Full player stats |
| `!sq exchange <amount>` | `ex` | Convert 100 acorns → 1 silver acorn |
| `!sq exchange_silver <amount>` | `exs` | Convert 10 silver → 1 emerald acorn |
| `!sq exchange_emerald <amount>` | `exe` | Convert 10 emerald → 1 golden acorn |
| `!sq sell <squirrel name>` | | Sell a squirrel for acorns |
| `!sq daily` | | Claim daily acorn bonus |
| `!sq leaderboard` | `lb`, `top` | Top catchers |
| `!sq bestiary` | `dex` | All squirrel species + discovery status |
| `!sq help` | | Show all commands |

## Squirrel Rarities

| Rarity | Examples | Drop Rate |
|--------|----------|-----------|
| ⬜ Common | Grey Squirrel, Red Squirrel, Chipmunk | ~70% |
| 🟢 Uncommon | Black Squirrel, White Squirrel, Fox Squirrel | ~20% |
| 🔵 Rare | Flying Squirrel, Albino Squirrel, Giant Squirrel | ~7% |
| 🟣 Epic | Crystal Squirrel, Shadow Squirrel | ~2% |
| 🟡 Legendary | Golden Squirrel, Cosmic Squirrel | ~0.5% |
| 🔴 Mythic | Mythic Nutcracker | ~0.1% |

Higher levels improve your chances of catching rare squirrels.

## Currency

| Currency | Value |
|----------|-------|
| 🌰 Acorns | Base currency |
| 🥈🌰 Silver Acorns | 100 acorns each |
| 💚🌰 Emerald Acorns | 1,000 acorns each |
| ✨🌰 Golden Acorns | 10,000 acorns each |

## Self-Hosting

### Prerequisites

- Python 3.10+
- PostgreSQL
- A Discord bot token

### Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/YOUR_USERNAME/SquirrelCatcher.git
   cd SquirrelCatcher
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   Or with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

3. **Create a `.env` file**

   ```
   DISCORD_BOT_TOKEN=your-bot-token
   DATABASE_URL=postgresql://user:password@localhost:5432/squirrel_catcher
   ```

4. **Create a Discord bot**

   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to **Bot** → **Add Bot**
   - Enable **Message Content Intent** under Privileged Gateway Intents
   - Copy the token into your `.env`

5. **Invite the bot to your server**

   - Go to **OAuth2 → URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Embed Links`, `Read Message History`
   - Open the generated URL to add the bot

6. **Run**

   ```bash
   # Start the bot
   python bot.py

   # Start the landing page server (optional)
   python server.py
   ```

### Deploy to Railway

The project includes a `Procfile` for [Railway](https://railway.app) deployment:

```
worker: python bot.py
web: python server.py
```

1. Connect your repo to Railway
2. Add a PostgreSQL plugin
3. Set `DISCORD_BOT_TOKEN` in environment variables
4. Deploy — Railway handles the rest

## Tech Stack

- **Python** with [discord.py](https://discordpy.readthedocs.io/)
- **PostgreSQL** with [asyncpg](https://github.com/MagicStack/asyncpg)
- **aiohttp** for the landing page server
- **Railway** for deployment

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

MIT
