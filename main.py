import discord
from discord.ext import commands
import os

# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.environ.get("DISCORD_CHANNEL_BOT_TOKEN")

# ============================================================
# ROLES — exact names as they appear in Discord (case sensitive)
# ============================================================

ADMIN_ROLES = ["Staff", "Mod"]

GAMES = [
    "VALORANT (PC)",
    "PUBG (MOBILE)",
    "LEAGUE OF LEGENDS (PC)",
    "FC26 (PS5)",
]

COUNTRY_ROLE_MAP = {
    "JORDAN": "JORDAN",
    "U.A.E.": "U.A.E.",
    "OMAN": "OMAN",
    "BAHRAIN": "BAHRAIN",
    "QATAR": "QATAR",
    "KUWAIT": "KUWAIT",
    "KSA": "KSA",
}

# University roles mapped to their country
UNIVERSITIES = {
    "JORDAN": [
        "Applied Science Private University",
        "AlHussein Technical University",
        "Al-Balqa Applied University",
        "Al al-Bayt University",
        "Al-Zaytoonah University of Jordan",
        "Amman Arab University",
        "Isra University",
        "German Jordanian University",
        "Hashimate",
        "Jarash University",
        "Jordan University of Science & Technology",
        "Luminus Technical University College",
        "Middle East University",
        "Princess Sumaya University for Technology",
        "Philadelphia University",
        "The University of Jordan",
        "University of Petra",
        "Yarmouk University",
        "Zarqa University",
    ],
    "U.A.E.": [
        "Abu Dhabi University",
        "Ajman University",
        "American University in the Emirates",
        "American University in Dubai",
        "American University of Sharjah",
        "British University",
        "Canadian University",
        "Hamdan Bin Mohammed Smart University",
        "Higher Colleges of Technology",
        "Heriot-Watt University",
        "Khalifa University",
        "Manipal Academy of Higher Education",
        "Mohamed Bin Zayed University of Artificial Intelligence",
        "Middlesex University",
        "Rochester Institute of Technology",
        "SAE Institute",
        "Skyline University College",
        "Symbiosis International University Dubai",
        "Synergy University",
        "United Arab Emirates University",
        "University of Dubai",
        "University of Sharjah",
        "University of Wollongong",
        "Zayed University",
    ],
    "OMAN": [
        "Middle East College",
        "Majan University College",
        "Modern College of Business and Science",
        "Arab Open University",
        "Gulf University",
    ],
    "BAHRAIN": [
        "Ahlia University",
        "University of Technology",
        "American University of Bahrain",
        "British University of Bahrain",
        "Kingdom University",
    ],
    "QATAR": [
        "Hamad Bin Khalifa University",
    ],
    "KUWAIT": [],
    "KSA": [
        "King Abdulaziz University",
],
}

# Roles that should never be treated as university roles
NON_UNI_ROLES = set(ADMIN_ROLES + GAMES + list(COUNTRY_ROLE_MAP.values()) + [
    "Server Booster", "GateKeeper", "carl-bot", "Bots", "Campus Masters Bot",
    "Verified", "Participant", "Muted", "Unverified","Male", 
    "Female", "Team Members", "Tally", "YAGPDB.xyz", "Ticket Tool",
    "@everyone"
])

# ============================================================
# HELPERS
# ============================================================

def make_channel_name(university: str, game: str) -> str:
    """Convert university + game into a valid Discord channel name.
    e.g. 'Khalifa University' + 'VALORANT (PC)' -> 'khalifa-university-valorant-pc'
    """
    uni_slug = university.lower()
    game_slug = game.lower()

    for char in ["'", ".", ",", "(", ")", "&"]:
        uni_slug = uni_slug.replace(char, "")
        game_slug = game_slug.replace(char, "")

    uni_slug = uni_slug.strip().replace(" ", "-")
    game_slug = game_slug.strip().replace(" ", "-")

    while "--" in uni_slug:
        uni_slug = uni_slug.replace("--", "-")
    while "--" in game_slug:
        game_slug = game_slug.replace("--", "-")

    return f"{uni_slug}-{game_slug}"


def make_category_name(country: str, game: str) -> str:
    """e.g. 'BAHRAIN' + 'VALORANT (PC)' -> 'BAHRAIN-VALORANT(PC)'"""
    game_slug = game.replace(" ", "")
    return f"{country}-{game_slug}"


def find_country_for_university(university: str) -> str | None:
    """Look up which country a university belongs to."""
    for country, unis in UNIVERSITIES.items():
        if university in unis:
            return country
    return None


def get_admin_roles(guild: discord.Guild) -> list:
    return [r for r in guild.roles if r.name in ADMIN_ROLES]


async def ensure_channel(guild: discord.Guild, university: str, game: str, country: str):
    """Create or update a university-game channel and its category."""

    category_name = make_category_name(country, game)
    channel_name = make_channel_name(university, game)

    # --- Find or create category ---
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        cat_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
        for admin_role in get_admin_roles(guild):
            cat_overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
        category = await guild.create_category(category_name, overwrites=cat_overwrites)
        print(f"  📁 Created category: {category_name}")

    # --- Build channel permission overwrites ---
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    for admin_role in get_admin_roles(guild):
        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)

    uni_role = discord.utils.get(guild.roles, name=university)
    if uni_role:
        overwrites[uni_role] = discord.PermissionOverwrite(view_channel=True)
    else:
        print(f"  ⚠️  University role not found: '{university}'")

    # --- Find or create channel ---
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await existing.edit(overwrites=overwrites, category=category)
        print(f"  🔄 Updated: #{channel_name}")
    else:
        await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"{university} | {game}"
        )
        print(f"  ✅ Created: #{channel_name}")

    return channel_name


async def ensure_other_channel(guild: discord.Guild, country: str, game: str):
    """
    Create or update a #country-other channel inside the country-game category.
    Visible to: Other role + admins only.
    e.g. category JORDAN-VALORANT(PC) -> #jordan-other
    """
    category_name = make_category_name(country, game)
    country_slug = country.lower().replace(".", "").replace("-", "")
    channel_name = f"{country_slug}-other"

    # --- Find or create category (same as university channels) ---
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        cat_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
        for admin_role in get_admin_roles(guild):
            cat_overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
        category = await guild.create_category(category_name, overwrites=cat_overwrites)
        print(f"  📁 Created category: {category_name}")

    # --- Build permission overwrites ---
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }

    # Admins can see
    for admin_role in get_admin_roles(guild):
        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)

    # Other role can see
    other_role = discord.utils.get(guild.roles, name="Other")
    if other_role:
        overwrites[other_role] = discord.PermissionOverwrite(view_channel=True)
    else:
        print(f"  ⚠️  'Other' role not found in Discord")

    # --- Find or create channel ---
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await existing.edit(overwrites=overwrites, category=category)
        print(f"  🔄 Updated: #{channel_name}")
    else:
        await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Students from unregistered universities in {country} | Discuss onboarding & eligibility"
        )
        print(f"  ✅ Created: #{channel_name}")

    return channel_name

# ============================================================
# BOT SETUP
# ============================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# ON READY — pre-create all known channels on startup
# ============================================================

@bot.event
async def on_ready():
    print(f"✅ Channel Bot online as {bot.user}")
    print("🔧 Setting up channels for all known universities...")

    for guild in bot.guilds:
        print(f"\n📡 Server: {guild.name}")
        for country, universities in UNIVERSITIES.items():
            for game in GAMES:
                # Create university channels
                for university in universities:
                    try:
                        await ensure_channel(guild, university, game, country)
                    except Exception as e:
                        print(f"  ❌ Error on {university} / {game}: {e}")
                # Create #country-other channel in every country-game category
                try:
                    await ensure_other_channel(guild, country, game)
                except Exception as e:
                    print(f"  ❌ Error creating other channel for {country} / {game}: {e}")

    print("\n✅ Startup channel setup complete!")

# ============================================================
# ON MEMBER UPDATE — auto-create channels when new uni role assigned
# ============================================================

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    new_roles = set(after.roles) - set(before.roles)
    if not new_roles:
        return

    guild = after.guild

    for role in new_roles:
        if role.name in NON_UNI_ROLES:
            continue

        country = find_country_for_university(role.name)
        if country:
            print(f"🆕 New university role: {role.name} ({country}) — ensuring channels...")
            for game in GAMES:
                try:
                    await ensure_channel(guild, role.name, game, country)
                except Exception as e:
                    print(f"  ❌ Error: {e}")
        else:
            print(f"ℹ️  Unknown role assigned: '{role.name}' — not in university list, skipping.")

# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin():
    async def predicate(ctx):
        if any(r.name in ADMIN_ROLES for r in ctx.author.roles):
            return True
        await ctx.send("❌ You don't have permission to run this command.")
        return False
    return commands.check(predicate)

# ============================================================
# COMMANDS
# ============================================================

@bot.command(name="setup-channels")
@is_admin()
async def setup_channels(ctx):
    """Re-run full channel setup and update all permissions."""
    msg = await ctx.send("🔧 Running full channel setup... this may take a moment.")
    count = 0

    for country, universities in UNIVERSITIES.items():
        for game in GAMES:
            for university in universities:
                try:
                    await ensure_channel(ctx.guild, university, game, country)
                    count += 1
                except Exception as e:
                    await ctx.send(f"❌ {university} / {game}: {e}")
            # Other channel per country-game category
            try:
                await ensure_other_channel(ctx.guild, country, game)
                count += 1
            except Exception as e:
                await ctx.send(f"❌ Other channel {country} / {game}: {e}")

    await msg.edit(content=f"✅ Done! Processed {count} channels.")


@bot.command(name="scan-roles")
@is_admin()
async def scan_roles(ctx):
    """
    Scans ALL current server members, finds university roles already assigned,
    and creates any missing channels for them.
    """
    msg = await ctx.send("🔍 Scanning all members for university roles...")
    guild = ctx.guild

    found_universities = set()

    for member in guild.members:
        for role in member.roles:
            if role.name in NON_UNI_ROLES:
                continue
            country = find_country_for_university(role.name)
            if country:
                found_universities.add((role.name, country))

    if not found_universities:
        await msg.edit(content="ℹ️ No university roles found on any members.")
        return

    await msg.edit(content=f"🔧 Found {len(found_universities)} universities in use — creating missing channels...")

    count = 0
    for university, country in sorted(found_universities):
        for game in GAMES:
            try:
                await ensure_channel(guild, university, game, country)
                count += 1
            except Exception as e:
                await ctx.send(f"❌ {university} / {game}: {e}")

    await ctx.send(f"✅ Scan complete! Processed {count} channels across {len(found_universities)} universities.")


@bot.command(name="add-university")
@is_admin()
async def add_university(ctx, country: str, *, university: str):
    """
    Manually add a new university and create its channels.
    Usage: !add-university UAE New York University Abu Dhabi
    Accepted countries: JORDAN, UAE, OMAN, BAHRAIN, QATAR, KUWAIT, KSA
    """
    country_map = {
        "UAE": "U.A.E.", "U.A.E.": "U.A.E.", "U.A.E": "U.A.E.",
        "JORDAN": "JORDAN", "OMAN": "OMAN",
        "BAHRAIN": "BAHRAIN", "QATAR": "QATAR", "KUWAIT": "KUWAIT",
        "KSA": "KSA"
    }
    country_key = country_map.get(country.upper())
    if not country_key:
        await ctx.send(
            f"❌ Country `{country}` not recognised.\n"
            f"Use: JORDAN, UAE, OMAN, BAHRAIN, QATAR, KUWAIT, KSA"
        )
        return

    msg = await ctx.send(f"🔧 Creating channels for **{university}** ({country_key})...")
    for game in GAMES:
        try:
            await ensure_channel(ctx.guild, university, game, country_key)
        except Exception as e:
            await ctx.send(f"❌ {game}: {e}")

    await msg.edit(content=f"✅ All channels created for **{university}** under {country_key}!")


@bot.command(name="channel-help")
@is_admin()
async def channel_help(ctx):
    await ctx.send(
        "**📋 Channel Bot Commands:**\n\n"
        "`!setup-channels` — Re-run full setup, create missing channels & update all permissions\n"
        "`!scan-roles` — Scan all current members, find university roles, create any missing channels\n"
        "`!add-university <COUNTRY> <University Name>` — Add a new university manually\n"
        "　　e.g. `!add-university UAE New York University Abu Dhabi`\n"
        "`!channel-help` — Show this message\n\n"
        "ℹ️ Each country-game category also contains a `#country-other` channel for unregistered university students."
    )

# ============================================================
# RUN
# ============================================================

bot.run(BOT_TOKEN)
