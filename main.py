import discord
from discord.ext import commands
import json
import os
from datetime import timedelta

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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# ================= BAN ================= #

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"✅ Banned {member.mention}\nReason: {reason}")
    except:
        await ctx.reply("❌ Failed to ban user.")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


# ================= UNBAN ================= #

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.reply(f"✅ Unbanned {user}")
    except:
        await ctx.reply("❌ Failed to unban user.")


@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


# ================= KICK ================= #

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    try:
        await member.kick(reason=reason)
        await ctx.reply(f"✅ Kicked {member.mention}\nReason: {reason}")
    except:
        await ctx.reply("❌ Failed to kick user.")


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


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
            return await ctx.reply("❌ Use m, h, or d.")

        await member.timeout(delta)
        await ctx.reply(f"✅ Muted {member.mention} for {duration}")

    except:
        await ctx.reply("❌ Failed to mute user.")


@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


# ================= UNMUTE ================= #

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.reply(f"✅ Unmuted {member.mention}")
    except:
        await ctx.reply("❌ Failed to unmute user.")


@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


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

    await ctx.reply(
        f"✅ Warned {member.mention}\nReason: {reason}"
    )


@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


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
        embed.description = "\n".join(
            [f"{i+1}. {w}" for i, w in enumerate(warns)]
        )

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

        await ctx.reply(
            f"✅ Cleared warnings for {member.mention}"
        )
    else:
        await ctx.reply("❌ User has no warnings.")


# ================= PURGE ================= #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):

    await ctx.channel.purge(limit=amount + 1)

    msg = await ctx.send(
        f"✅ Deleted {amount} messages."
    )

    await msg.delete(delay=3)


@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("❌ You don't have permission to use this command.")


# ================= ROLE ================= #

@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, *, role_name):

    role = discord.utils.get(
        ctx.guild.roles,
        name=role_name
    )

    if role is None:
        return await ctx.reply("❌ Role not found.")

    try:
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.reply(
                f"✅ Role removed from {member.mention}"
            )
        else:
            await member.add_roles(role)
            await ctx.reply(
                f"✅ Role added to {member.mention}"
            )
    except:
        await ctx.reply("❌ Failed to edit role.")


# ================= LOCK ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = False

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.reply("✅ Channel locked.")


# ================= UNLOCK ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):

    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = None

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.reply("✅ Channel unlocked.")


# ================= SLOWMODE ================= #

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):

    try:
        await ctx.channel.edit(
            slowmode_delay=seconds
        )

        await ctx.reply(
            f"✅ Slowmode set to {seconds} seconds."
        )
    except:
        await ctx.reply("❌ Failed to set slowmode.")
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

    embed = discord.Embed(
        title=f"User Info - {member}",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="User ID",
        value=member.id,
        inline=False
    )

    embed.add_field(
        name="Joined Server",
        value=member.joined_at.strftime("%d/%m/%Y"),
        inline=False
    )

    embed.add_field(
        name="Account Created",
        value=member.created_at.strftime("%d/%m/%Y"),
        inline=False
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    await ctx.reply(embed=embed)


# ================= SERVERINFO ================= #

@bot.command()
async def serverinfo(ctx):

    guild = ctx.guild

    embed = discord.Embed(
        title=f"{guild.name}",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="Members",
        value=guild.member_count
    )

    embed.add_field(
        name="Roles",
        value=len(guild.roles)
    )

    embed.add_field(
        name="Channels",
        value=len(guild.channels)
    )

    embed.add_field(
        name="Owner",
        value=guild.owner
    )

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
        await ctx.reply(
            "❌ You don't have permission to use this command."
        )


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

    await bot.process_commands(message)


@bot.command()
async def snipe(ctx):

    if ctx.channel.id not in sniped_messages:
        return await ctx.reply(
            embed=discord.Embed(
                title="Snipe",
                description="No deleted messages found.",
                color=discord.Color.red()
            )
        )

    content, author = sniped_messages[ctx.channel.id]

    embed = discord.Embed(
        title="Deleted Message",
        description=content,
        color=discord.Color.orange()
    )

    embed.set_footer(
        text=f"Author: {author}"
    )

    await ctx.reply(embed=embed)


# ================= PLAY ================= #

voice_clients = {}

@bot.command()
async def play(ctx, *, url):

    if not ctx.author.voice:
        return await ctx.reply(
            embed=discord.Embed(
                description="❌ Join a voice channel first.",
                color=discord.Color.red()
            )
        )

    vc = ctx.voice_client

    if vc is None:
        vc = await ctx.author.voice.channel.connect()

    source = discord.FFmpegPCMAudio(url)

    vc.play(source)

    embed = discord.Embed(
        title="🎵 Music",
        description="Playing audio.",
        color=discord.Color.green()
    )

    await ctx.reply(embed=embed)


# ================= LEAVE ================= #

@bot.command()
async def leave(ctx):

    if ctx.voice_client:

        await ctx.voice_client.disconnect()

        embed = discord.Embed(
            description="✅ Left voice channel.",
            color=discord.Color.green()
        )

        await ctx.reply(embed=embed)

    else:

        embed = discord.Embed(
            description="❌ Not connected to a voice channel.",
            color=discord.Color.red()
        )

        await ctx.reply(embed=embed)
 bot.run(TOKEN)
