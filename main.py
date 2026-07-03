import discord
from discord.ext import commands
import json
import os
from datetime import timedelta

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="*", intents=intents)

WARN_FILE = "warnings.json"

if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w") as f:
        json.dump({}, f)


def load_warnings():
    with open(WARN_FILE, "r") as f:
        return json.load(f)


def save_warnings(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)


def make_embed(title=None, description=None, color=discord.Color.blurple()):
    return discord.Embed(title=title, description=description, color=color)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ================= BAN ================= #

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.ban(reason=reason)
        embed = make_embed(
            title="User Banned",
            description=f"✅ {member.mention} has been banned.\n**Reason:** {reason}",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)
    except Exception:
        embed = make_embed(
            title="Error",
            description="❌ Failed to ban user.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(embed=make_embed(
            "Invalid User",
            "❌ Please mention a valid user to ban.",
            discord.Color.red()
        ))


# ================= UNBAN ================= #

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        banned_users = await ctx.guild.bans()
        target_user = None

        for ban_entry in banned_users:
            if ban_entry.user.id == user_id:
                target_user = ban_entry.user
                break

        if target_user is None:
            return await ctx.reply(embed=make_embed(
                title="User Not Banned",
                description="❌ That user is not banned or the ID is invalid.",
                color=discord.Color.red()
            ))

        await ctx.guild.unban(target_user)

        embed = make_embed(
            title="User Unbanned",
            description=f"✅ {target_user} has been unbanned.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)

    except Exception:
        embed = make_embed(
            title="Error",
            description="❌ Failed to unban user.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)


@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(embed=make_embed(
            "Invalid User ID",
            "❌ Please provide a valid numeric user ID.",
            discord.Color.red()
        ))


# ================= KICK ================= #

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        embed = make_embed(
            title="User Kicked",
            description=f"✅ {member.mention} has been kicked.\n**Reason:** {reason}",
            color=discord.Color.orange()
        )
        await ctx.reply(embed=embed)
    except Exception:
        embed = make_embed(
            title="Error",
            description="❌ Failed to kick user.",
            color=discord.Color.red()
        )
        await ctx.reply(embed=embed)


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= MUTE ================= #

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str):
    try:
        unit = duration[-1]
        amount = int(duration[:-1])

        if unit == "m":
            delta = timedelta(minutes=amount)
        elif unit == "h":
            delta = timedelta(hours=amount)
        elif unit == "d":
            delta = timedelta(days=amount)
        else:
            return await ctx.reply(embed=make_embed(
                "Invalid Duration",
                "❌ Use m, h, or d.",
                discord.Color.red()
            ))

        await member.timeout(delta)
        embed = make_embed(
            title="Member Muted",
            description=f"✅ {member.mention} has been muted for **{duration}**.",
            color=discord.Color.orange()
        )
        await ctx.reply(embed=embed)

    except ValueError:
        await ctx.reply(embed=make_embed(
            "Invalid Duration",
            "❌ Use a valid duration like `10m`, `2h`, or `1d`.",
            discord.Color.red()
        ))
    except Exception:
        await ctx.reply(embed=make_embed("Error", "❌ Failed to mute user.", discord.Color.red()))


@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= UNMUTE ================= #

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        embed = make_embed(
            title="Member Unmuted",
            description=f"✅ {member.mention} has been unmuted.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)
    except Exception:
        await ctx.reply(embed=make_embed("Error", "❌ Failed to unmute user.", discord.Color.red()))


@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= WARN ================= #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    data = load_warnings()

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in data:
        data[guild_id] = {}

    if user_id not in data[guild_id]:
        data[guild_id][user_id] = []

    data[guild_id][user_id].append(reason)
    save_warnings(data)

    embed = make_embed(
        title="User Warned",
        description=f"✅ {member.mention} has been warned.\n**Reason:** {reason}",
        color=discord.Color.gold()
    )
    await ctx.reply(embed=embed)


@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= WARNINGS ================= #

@bot.command()
async def warnings(ctx, member: discord.Member):
    data = load_warnings()

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    warns = data.get(guild_id, {}).get(user_id, [])

    embed = discord.Embed(
        title=f"Warnings for {member}",
        color=discord.Color.orange()
    )

    if not warns:
        embed.description = "No warnings."
    else:
        embed.description = "\n".join(f"{i+1}. {w}" for i, w in enumerate(warns))

    await ctx.reply(embed=embed)


# ================= CLEAR WARNINGS ================= #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarnings(ctx, member: discord.Member):
    data = load_warnings()

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id in data and user_id in data[guild_id]:
        data[guild_id][user_id] = []
        save_warnings(data)
        await ctx.reply(embed=make_embed(
            title="Warnings Cleared",
            description=f"✅ Cleared warnings for {member.mention}.",
            color=discord.Color.green()
        ))
    else:
        await ctx.reply(embed=make_embed(
            title="No Warnings",
            description="❌ User has no warnings.",
            color=discord.Color.red()
        ))


# ================= PURGE ================= #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=make_embed(
        title="Purge Complete",
        description=f"✅ Deleted {amount} messages.",
        color=discord.Color.green()
    ))
    await msg.delete(delay=3)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= ROLE ================= #

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name):
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role is None:
        return await ctx.reply(embed=make_embed(
            "Role Not Found",
            "❌ Role not found.",
            discord.Color.red()
        ))

    try:
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.reply(embed=make_embed(
                "Role Removed",
                f"✅ Role removed from {member.mention}.",
                discord.Color.green()
            ))
        else:
            await member.add_roles(role)
            await ctx.reply(embed=make_embed(
                "Role Added",
                f"✅ Role added to {member.mention}.",
                discord.Color.green()
            ))
    except Exception:
        await ctx.reply(embed=make_embed("Error", "❌ Failed to edit role.", discord.Color.red()))


# ================= LOCK ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False

    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    await ctx.reply(embed=make_embed("Channel Locked", "✅ Channel locked.", discord.Color.red()))


# ================= UNLOCK ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None

    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    await ctx.reply(embed=make_embed("Channel Unlocked", "✅ Channel unlocked.", discord.Color.green()))


# ================= SLOWMODE ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.reply(embed=make_embed(
            title="Slowmode Updated",
            description=f"✅ Slowmode set to **{seconds}** seconds.",
            color=discord.Color.green()
        ))
    except Exception:
        await ctx.reply(embed=make_embed("Error", "❌ Failed to set slowmode.", discord.Color.red()))


# ================= PING ================= #

@bot.command()
async def ping(ctx):
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {round(bot.latency * 1000)}ms",
        color=discord.Color.green()
    )
    await ctx.reply(embed=embed)


# ================= AVATAR ================= #

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author

    embed = discord.Embed(
        title=f"{member}'s Avatar",
        color=discord.Color.blurple()
    )
    embed.set_image(url=member.display_avatar.url)

    await ctx.reply(embed=embed)


# ================= USERINFO ================= #

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author

    joined_at = member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Unknown"

    embed = discord.Embed(
        title=f"User Info - {member}",
        color=discord.Color.blue()
    )

    embed.add_field(name="User ID", value=str(member.id), inline=False)
    embed.add_field(name="Joined Server", value=joined_at, inline=False)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%d/%m/%Y"), inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)

    await ctx.reply(embed=embed)


# ================= SERVERINFO ================= #

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.gold()
    )

    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Owner", value=str(guild.owner), inline=False)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.reply(embed=embed)


# ================= MEMBERCOUNT ================= #

@bot.command()
async def membercount(ctx):
    embed = discord.Embed(
        title="Member Count",
        description=f"👥 {ctx.guild.member_count}",
        color=discord.Color.green()
    )
    await ctx.reply(embed=embed)


# ================= POLL ================= #

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=discord.Color.blue()
    )

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")


# ================= SAY ================= #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)


@say.error
async def say_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=make_embed(
            "Permission Error",
            "❌ You don't have permission to use this command.",
            discord.Color.red()
        ))


# ================= SNIPE ================= #

sniped_messages = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    sniped_messages[message.channel.id] = (
        message.content,
        message.author
    )


@bot.command()
async def snipe(ctx):
    if ctx.channel.id not in sniped_messages:
        return await ctx.reply(embed=discord.Embed(
            title="Snipe",
            description="No deleted messages found.",
            color=discord.Color.red()
        ))

    content, author = sniped_messages[ctx.channel.id]

    embed = discord.Embed(
        title="Deleted Message",
        description=content if content else "*No text content*",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Author: {author}")

    await ctx.reply(embed=embed)


# ================= PLAY ================= #

@bot.command()
async def play(ctx, *, url):
    if not ctx.author.voice:
        return await ctx.reply(embed=discord.Embed(
            description="❌ Join a voice channel first.",
            color=discord.Color.red()
        ))

    vc = ctx.voice_client

    if vc is None:
        vc = await ctx.author.voice.channel.connect()

    try:
        source = discord.FFmpegPCMAudio(url)
        vc.play(source)

        embed = discord.Embed(
            title="🎵 Music",
            description="Playing audio.",
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed)
    except Exception:
        await ctx.reply(embed=discord.Embed(
            title="Error",
            description="❌ Failed to play audio.",
            color=discord.Color.red()
        ))


# ================= LEAVE ================= #

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.reply(embed=discord.Embed(
            description="✅ Left voice channel.",
            color=discord.Color.green()
        ))
    else:
        await ctx.reply(embed=discord.Embed(
            description="❌ Not connected to a voice channel.",
            color=discord.Color.red()
        ))


bot.run(TOKEN)
