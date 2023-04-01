import os
import time

import discord
from discord.ext import commands

from botConfig import *
import logFunctions as log

import tracemalloc
tracemalloc.start()

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

class marketWrangler(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.startTime = time.time()
    
    async def setup_hook(self):
        cogs = [i[:-3] for i in os.listdir(r".\cogs") if i.endswith(".py")]
        for cog in cogs: await wrangler.load_extension(f"cogs.{cog}")

wrangler = marketWrangler()

#ping
@wrangler.command(name="ping", description="Pings the bot")
async def ping(interaction):
    await interaction.channel.send(f"Pong! Latency: {round(wrangler.latency * 1000)}ms")

#stats
@wrangler.command(name="stats", description="Shows the bot stats")
async def stats(interaction):
    if interaction.author.id == ownerID and isinstance(interaction.channel, discord.DMChannel):
        serverCount = len(wrangler.guilds)
        memberCount = len(set(wrangler.get_all_members()))
        fileSize = round(get_size(r".\ytData") / 1040400, 2)
        fileCount = len(os.listdir(r".\ytData"))
        timeSinceStart = time.strftime('%H:%M:%S', time.gmtime(time.time() - wrangler.startTime))
        botRunningSince = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(wrangler.startTime))
        embed = discord.Embed(title="Bot stats", color=0x00ff00)
        embed.add_field(name="Bot info:", value=f"Bot uptime: {timeSinceStart} seconds\nBot running since: {botRunningSince}\nBot latency: {round(wrangler.latency * 1000)} ms", inline=False)
        embed.add_field(name="Server info:", value=f"Server count: {serverCount}\nTotal members: {memberCount}", inline=False)
        embed.add_field(name="File system:", value=f"Music file count: {fileCount}\nTotal music file size: {fileSize} MB", inline=False)
        await interaction.channel.send(embed=embed)
    else: pass

#slash commands sync
@wrangler.command(name="sync", description="Syncs the bot commands")
async def sync(interaction):
    if interaction.author.id == ownerID and isinstance(interaction.channel, discord.DMChannel):
        await wrangler.tree.sync()
        await interaction.message.add_reaction("✅")
    else: pass

#run the bot
wrangler.run(botToken) #log_handler=log.logHandler