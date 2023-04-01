from discord.ext import commands
import os
from botConfig import *

import logFunctions as log

import tracemalloc
tracemalloc.start()

async def setup(bot):
    log.logInfo("Loading cogTools", "setup.cogs")
    await bot.add_cog(cogTools(bot))

class cogTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="loadCog", description="Loads a cog")
    async def loadCog(self, interaction, cogName):
        if interaction.author.id == ownerID: pass
        if cogName not in adminCogs: pass
        await self.bot.load_extension(f"cogs.{cogName}")

    @commands.command(name="unloadCog", description="Unloads a cog")
    async def unloadCog(self, interaction, cogName):
        if interaction.author.id == ownerID: pass
        if cogName not in adminCogs: pass
        await self.bot.unload_extension(f"cogs.{cogName}")

    @commands.command(name="reloadCog", description="Reloads a cog")
    async def reloadCog(self, interaction, cogName):
        if interaction.author.id == ownerID: pass
        if cogName not in adminCogs: pass
        await self.bot.reload_extension(f"cogs.{cogName}")

    @commands.command(name="reloadAll", description="Reloads all cogs")
    async def reloadAll(self, interaction):
        if interaction.author.id == ownerID: pass
        allCogs = [i[:-3] for i in os.listdir(r".\cogs") if i.endswith(".py")]
        reloadableCogs = [i for i in allCogs if i not in adminCogs]
        for cog in reloadableCogs:
            await self.bot.reload_extension(f"cogs.{cog}") 
        await interaction.channel.send(f"Reloaded {len(reloadableCogs)} cogs")