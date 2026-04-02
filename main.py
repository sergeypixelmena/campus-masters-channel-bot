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

# University roles mapped to their country — EXACT NAMES FROM DISCORD
UNIVERSITIES = {
    "JORDAN": [
        "Applied Science Private University",
        "Al-Ahliyya Amman University",
        "AlHussein Technical University",
        "Al-Balqa Applied University",
        "Al al-Bayt University",
        "Al-Zaytoonah University of Jordan",
        "Amman Arab University",
        "Islamic University of Madinah",
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
        "Irbid National University",
        "Jadara University",
        "American University of Madaba",
        "Mutah University",
        "Tafila Technical University",
        "Arab Open University Jordan",
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
        "Murdoch University",
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
        "Metaverse Age Training Institute",
        "Bath Spa University",
        "Al Ain University",
        "Dubai Medical University",
        "University of Birmingham",
        "New York University Abu Dhabi",
        "Amity University Dubai",
        "Sorbonne University Abu Dhabi",
        "Istec Business School Middle East",
        "Emirates Aviation University",
    ],
    "OMAN": [
        "Middle East College",
        "Majan University College",
        "Modern College of Business and Science",
        "German University of Technology in Oman",
        "Sultan Qaboos University",
    ],
    "BAHRAIN": [
        "Arab Open University",
        "Gulf University",
        "Ahlia University",
        "University of Technology",
        "American University of Bahrain",
        "British University of Bahrain",
        "Kingdom University",
    ],
    "QATAR": [
        "Carnegie Melon University",
        "Georgetown University",
        "Hamad Bin Khalifa University",
        "Northwestern University",
        "Texas A&M University",
        "Virginia Commonwealth University",
        "University of Doha for Science and Technology",
    ],
    "KUWAIT": [
        "American University of the Middle East",
        "Arab Open University Kuwait",
        "Gulf University for Science and Technology",
    ],
    "KSA": [
        "King Abdulaziz University",
        "King Saud University",
        "Princess Nourah Bint Abdulrahman University",
        "Alfaisal University",
        "King Fahd University for Petroleum and Minerals",
        "Dar Al-Hekma College",
        "Prince Sattam bin Abdulaziz University",
        "Prince Mohammed Bin Fahd University",
        "966 Innovation Hub",
        "University of Jeddah",
        "Saudi Electronic University",
        "University of Business and Technology",
        "Islamic University of Madinah",
        "Northern Border University",
    ],
}

# Roles that should never be treated as university roles
NON_UNI_ROLES = set(ADMIN_ROLES + GAMES + list(COUNTRY_ROLE_MAP.values()) + [
    "Server Booster", "GateKeeper", "carl-bot", "Bots", "Campus Masters Bot",
    "Verified", "Participant", "Muted", "Unverified", "Male",
    "Female", "Team Members", "Tally", "YAGPDB.xyz", "Ticket Tool",
    "@everyone"
])

# ============================================================
# HELPERS
# ============================================================

def make_channel_name(university: str) -> str:
    """Convert university name to channel name (slugified)."""
    channel_slug = university.lower()
    for char in ["'", ".", ",", "(", ")", "&"]:
        channel_slug = channel_slug.replace(char, "")
    channel_slug = channel_slug.strip().replace(" ", "-")
    while "--" in channel_slug:
        channel_slug = channel_slug.replace("--", "-")
    return channel_slug


def find_country_for_university(university: str) -> str | None:
    """Find which country a university belongs to."""
    for country, unis in UNIVERSITIES.items():
        if university in unis:
            return country
    return None


def get_admin_roles(guild: discord.Guild) -> list:
    """Get all admin roles in the guild."""
    return [r for r in guild.roles if r.name in ADMIN_ROLES]


async def ensure_university_channel(guild: discord.Guild, university: str, country: str):
    """
    Create or update a channel for a university.
    Then ensure it has threads for all 4 games.
    """
    category_name = country
    channel_name = make_channel_name(university)
    
    # Step 1: Ensure category exists
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        cat_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
        for admin_role in get_admin_roles(guild):
            cat_overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
        category = await guild.create_category(category_name, overwrites=cat_overwrites)
        print(f"  📁 Created category: {category_name}")
    
    # Step 2: Ensure channel exists
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
    
    existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if existing_channel:
        await existing_channel.edit(overwrites=overwrites, category=category)
        channel = existing_channel
        print(f"  🔄 Updated channel: #{channel_name}")
    else:
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"{university} | Campus Masters"
        )
        print(f"  ✅ Created channel: #{channel_name}")
    
    # Step 3: Ensure threads exist for each game
    for game in GAMES:
        thread_name = f"{game} - {university}"
        
        # Check if thread already exists
        existing_thread = discord.utils.get(channel.threads, name=thread_name)
        if existing_thread:
            print(f"    ℹ️  Thread exists: 🧵 {thread_name}")
        else:
            try:
                thread = await channel.create_thread(
                    name=thread_name,
                    auto_archive_duration=10080  # 7 days
                )
                print(f"    ✅ Created thread: 🧵 {thread_name}")
            except Exception as e:
                print(f"    ❌ Error creating thread for {game}: {e}")
    
    return channel_name


async def ensure_other_channel(guild: discord.Guild, country: str):
    """
    Create or update a #country-other channel inside one shared
    'Other Universities' category. One channel per country only.
    """
    OTHER_CATEGORY_NAME = "Other Universities"
    country_slug = country.lower().replace(".", "").replace("-", "")
    channel_name = f"{country_slug}-other"
    
    # Find or create the shared Other Universities category
    category = discord.utils.get(guild.categories, name=OTHER_CATEGORY_NAME)
    if not category:
        cat_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False)
        }
        for admin_role in get_admin_roles(guild):
            cat_overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
        category = await guild.create_category(OTHER_CATEGORY_NAME, overwrites=cat_overwrites)
        print(f"  📁 Created category: {OTHER_CATEGORY_NAME}")
    
    # Build permission overwrites
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False)
    }
    for admin_role in get_admin_roles(guild):
        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
    
    other_role = discord.utils.get(guild.roles, name="Other")
    if other_role:
        overwrites[other_role] = discord.PermissionOverwrite(view_channel=True)
    else:
        print(f"  ⚠️  'Other' role not found in Discord")
    
    # Find or create channel
    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await existing.edit(overwrites=overwrites, category=category)
        print(f"  🔄 Updated: #{channel_name}")
    else:
        await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Students from unregistered universities in {country}"
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
# ON READY
# ============================================================

@bot.event
async def on_ready():
    print(f"✅ Channel Bot online as {bot.user}")
    print("🔧 Setting up channels for all known universities...")

    for guild in bot.guilds:
        print(f"\n📡 Server: {guild.name}")
        for country, universities in UNIVERSITIES.items():
            for university in universities:
                try:
                    await ensure_university_channel(guild, university, country)
                except Exception as e:
                    print(f"  ❌ Error on {university}: {e}")
            # Create one #country-other channel per country in Other Universities category
            try:
                await ensure_other_channel(guild, country)
            except Exception as e:
                print(f"  ❌ Error creating other channel for {country}: {e}")

    print("\n✅ Startup channel setup complete!")

# ============================================================
# ON MEMBER UPDATE
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
            print(f"🆕 New university role: {role.name} ({country}) — ensuring channel and threads...")
            try:
                await ensure_university_channel(guild, role.name, country)
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
        for university in universities:
            try:
                await ensure_university_channel(ctx.guild, university, country)
                count += 1
            except Exception as e:
                await ctx.send(f"❌ {university}: {e}")
        # One other channel per country
        try:
            await ensure_other_channel(ctx.guild, country)
            count += 1
        except Exception as e:
            await ctx.send(f"❌ Other channel {country}: {e}")

    await msg.edit(content=f"✅ Done! Processed {count} channels.")


@bot.command(name="scan-roles")
@is_admin()
async def scan_roles(ctx):
    """Scans all members, finds university roles, creates missing channels."""
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
        try:
            await ensure_university_channel(guild, university, country)
            count += 1
        except Exception as e:
            await ctx.send(f"❌ {university}: {e}")

    await ctx.send(f"✅ Scan complete! Processed {count} channels across {len(found_universities)} universities.")


@bot.command(name="add-university")
@is_admin()
async def add_university(ctx, country: str, *, university: str):
    """
    Manually add a new university and create its channel + threads.
    Usage: !add-university UAE "Abu Dhabi University"
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

    msg = await ctx.send(f"🔧 Creating channel + threads for **{university}** ({country_key})...")
    try:
        await ensure_university_channel(ctx.guild, university, country_key)
        await msg.edit(content=f"✅ Channel and 4 game threads created for **{university}** under {country_key}!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")


@bot.command(name="restructure-channels")
@is_admin()
async def restructure_channels(ctx):
    """
    Restructure existing channels to match new university-based structure.
    - Renames categories to country names only
    - Reorganizes universities into their country categories
    - Creates game threads for each university
    - Deletes old game-only categories (Valorant, LOL, PUBG, FC26)
    Only affects categories/channels matching the old structure.
    PROTECTED CATEGORIES (never deleted): Admin Stuff, Support, Text Channels, 
    League of Legends, FIFA26, PUBG, Valorant, Campus Masters Season 1 Teams, 
    Campus Masters Season 1 Teams VC
    """
    guild = ctx.guild
    msg = await ctx.send("🔧 Starting restructure... this may take a moment.")
    
    # Categories that should NEVER be deleted
    PROTECTED_CATEGORIES = {
        "Admin Stuff",
        "Support",
        "Text Channels",
        "League of Legends",
        "FIFA26",
        "PUBG",
        "Valorant",
        "Campus Masters Season 1 Teams",
        "Campus Masters Season 1 Teams VC",
    }
    
    reorganized = 0
    deleted_categories = 0
    
    print(f"\n🔄 Restructuring {guild.name}...")
    print(f"🛡️  Protected categories: {', '.join(PROTECTED_CATEGORIES)}")
    
    # Step 1: Reorganize all universities into their country categories
    print(f"\n📂 Step 1: Creating/updating university channels by country...")
    for country, universities in UNIVERSITIES.items():
        for university in universities:
            try:
                await ensure_university_channel(guild, university, country)
                reorganized += 1
            except Exception as e:
                print(f"  ❌ Error with {university}: {e}")
                await ctx.send(f"❌ Error with {university}: {e}")
    
    # Step 2: Delete old game-only categories (those that don't match country names)
    print(f"\n🗑️  Step 2: Cleaning up old game-only categories...")
    old_category_names = [
        "VALORANT", "VALORANT (PC)", "VALORANT PC",
        "LEAGUE OF LEGENDS", "LOL", "LEAGUE-OF-LEGENDS", "LOL (PC)",
        "PUBG", "PUBG (MOBILE)", "PUBG MOBILE",
        "FC26", "FIFA26", "FC26 (PS5)", "FIFA 26",
    ]
    
    for category in guild.categories:
        # NEVER delete protected categories
        if category.name in PROTECTED_CATEGORIES:
            print(f"  🛡️  Protected: {category.name} (skipped)")
            continue
        
        # Check if this is an old game-only category (not a country name)
        is_country_category = category.name in COUNTRY_ROLE_MAP.keys()
        is_old_game_category = any(game in category.name.upper() for game in old_category_names)
        
        if is_old_game_category and not is_country_category:
            try:
                # Delete all channels in the category first
                for channel in category.channels:
                    await channel.delete()
                    print(f"  🗑️  Deleted channel: #{channel.name}")
                
                # Then delete the category
                await category.delete()
                print(f"  🗑️  Deleted category: {category.name}")
                deleted_categories += 1
            except Exception as e:
                print(f"  ⚠️  Error deleting {category.name}: {e}")
    
    # Final summary
    summary = (
        f"✅ **Restructure Complete!**\n\n"
        f"📝 **University channels/threads created/updated:** {reorganized}\n"
        f"🗑️  **Old game categories deleted:** {deleted_categories}\n"
        f"🛡️  **Protected categories:** {len(PROTECTED_CATEGORIES)} (untouched)"
    )
    
    await msg.edit(content=summary)
    print(f"\n{summary}\n")


@bot.command(name="create-team")
@is_admin()
async def create_team(ctx, channel_name: str, *, team_role_name: str):
    """
    Create text and voice channels for a team.
    Usage: !create-team jordan-hu-alg-valorant "Team Algharbi"
    """
    guild = ctx.guild

    text_category = discord.utils.get(guild.categories, name="Campus Masters Season 1 Teams")
    vc_category = discord.utils.get(guild.categories, name="Campus Masters Season 1 Teams VC")

    if not text_category or not vc_category:
        await ctx.send(
            "❌ Could not find team categories.\n"
            "Make sure these exist:\n"
            "- `Campus Masters Season 1 Teams`\n"
            "- `Campus Masters Season 1 Teams VC`",
            delete_after=15
        )
        return

    team_role = discord.utils.get(guild.roles, name=team_role_name)
    if not team_role:
        await ctx.send(
            f"❌ Role **{team_role_name}** not found in Discord.\n"
            f"Create the role first then run this command.",
            delete_after=10
        )
        return

    # Permissions for text channel
    overwrites_text = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        team_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }

    # Permissions for voice channel
    overwrites_vc = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        team_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
    }

    # Add admin and staff roles
    for role_name in ADMIN_ROLES + ["Campus Masters Bot"]:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            overwrites_text[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True
            )
            overwrites_vc[role] = discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True, mute_members=True
            )

    # Create text channel
    text_channel = await guild.create_text_channel(
        name=channel_name,
        category=text_category,
        overwrites=overwrites_text
    )

    # Create voice channel
    vc_channel = await guild.create_voice_channel(
        name=channel_name,
        category=vc_category,
        overwrites=overwrites_vc
    )

    await ctx.send(
        f"✅ **Team channels created!**\n"
        f"📝 {text_channel.mention}\n"
        f"🔊 {vc_channel.name}\n"
        f"🎭 Access granted to: **{team_role_name}**",
        delete_after=15
    )

    print(f"✅ Team created: #{channel_name} | Role: {team_role_name}")


@bot.command(name="channel-help")
@is_admin()
async def channel_help(ctx):
    await ctx.send(
        "**📋 Channel Bot Commands:**\n\n"
        "`!setup-channels` — Re-run full setup, create all university channels with game threads\n"
        "`!scan-roles` — Scan all current members, find university roles, create any missing channels\n"
        "`!add-university <COUNTRY> <University Name>` — Add a new university channel + threads\n"
        "　　e.g. `!add-university UAE \"Abu Dhabi University\"`\n"
        "`!restructure-channels` — Restructure to new university-based organization (one-time migration)\n"
        "`!create-team <channel-name> <Team Role Name>` — Create text and voice channels for a team\n"
        "　　e.g. `!create-team jordan-hu-alg-valorant Team Algharbi`\n"
        "`!channel-help` — Show this message\n\n"
        "📌 **Structure:** Country Category → University Channel → Game Threads (4 per university)"
    )

# ============================================================
# RUN
# ============================================================

bot.run(BOT_TOKEN)
