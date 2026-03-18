import re
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands

# ========================
# CONFIG
# ========================

TOKEN = "MTQ4MzYzODIyNzMyMjc5ODE0MA.G3eDPu.ICO7e9QoLnw9B1BFOIHxUJFwKaOxf6dGxGJCFw"
PREFIX = "+"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

sniped_messages = {}
blacklisted_users = set()

# ========================
# UTILS (temps)
# ========================

def parse_time(time_str: str):
    match = re.fullmatch(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)

    return None

# ========================
# BOT READY
# ========================

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# ========================
# SNIPE EVENT
# ========================

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
    }

# ========================
# CLEAR
# ========================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"✅ {amount} messages supprimés")
    await asyncio.sleep(3)
    await msg.delete()

# ========================
# SNIPE
# ========================

@bot.command()
async def snipe(ctx):
    data = sniped_messages.get(ctx.channel.id)

    if not data:
        return await ctx.send("Aucun message supprimé")

    embed = discord.Embed(
        description=data["content"],
        color=discord.Color.orange()
    )
    embed.set_author(name=data["author"])

    await ctx.send(embed=embed)

# ========================
# LOCK
# ========================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Salon verrouillé")

# ========================
# UNLOCK
# ========================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Salon déverrouillé")

# ========================
# RENEW
# ========================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def renew(ctx):
    new = await ctx.channel.clone()
    await new.send("♻️ Salon recréé")
    await ctx.channel.delete()

# ========================
# SAY
# ========================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

# ========================
# BAN
# ========================

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.ban(reason=reason)

    embed = discord.Embed(
        title="✅ Le membre a été banni",
        description=f"{member.mention} a été banni",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# UNBAN
# ========================

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int, *, reason="Aucune raison"):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    embed = discord.Embed(
        title="✅ Le membre a été débanni",
        description=f"@{user.name} a été débanni",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# MUTE
# ========================

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason="Aucune raison"):
    delta = parse_time(duration)
    if delta is None:
        return await ctx.send("Format invalide")

    await member.timeout(delta)

    embed = discord.Embed(
        title="🔇 Le membre a été mute",
        description=f"{member.mention} mute pendant {duration}",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# UNMUTE
# ========================

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.timeout(None)

    embed = discord.Embed(
        title="🔊 Le membre a été unmute",
        description=f"{member.mention} a été unmute",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# BLACKLIST (BL)
# ========================

@bot.command()
@commands.has_permissions(ban_members=True)
async def bl(ctx, member: discord.Member, *, reason="Blacklist"):
    blacklisted_users.add(member.id)
    await member.ban(reason=reason)

    embed = discord.Embed(
        title="⛔ Le membre a été blacklist",
        description=f"{member.mention} blacklist + ban",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# UNBLACKLIST (UNBL)
# ========================

@bot.command()
@commands.has_permissions(ban_members=True)
async def unbl(ctx, user_id: int, *, reason="Unblacklist"):
    blacklisted_users.discard(user_id)
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    embed = discord.Embed(
        title="✅ Retiré de la blacklist",
        description=f"@{user.name} débanni",
        color=0x2ecc71
    )
    embed.add_field(name="Raison", value=reason)

    await ctx.send(embed=embed)

# ========================
# RUN BOT
# ========================

bot.run(TOKEN)