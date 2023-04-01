from discord.ext import commands, tasks
from discord import app_commands
from discord import FFmpegOpusAudio
import discord
import re
import urllib.request
from pytube import YouTube
import os
import asyncio
import time
from colorama import Fore, Back, Style
import datetime
import logFunctions as log

import tracemalloc
tracemalloc.start()

class playerButtons(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    @discord.ui.button(label="Play", style=discord.ButtonStyle.gray, emoji="▶️")
    async def playButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            if voiceClient.is_paused():
                voiceClient.resume()
                await interaction.response.edit_message(view=self)
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)
    
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.grey, emoji="⏸️")
    async def pauseButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            if voiceClient.is_playing():
                voiceClient.pause()
                await interaction.response.edit_message(view=self)
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.gray, emoji="⏹️")
    async def stopButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            if voiceClient.is_playing():
                voiceClient.stop()
                embed = discord.Embed(title="Music Player", description="Stopped", color=0x00ff00)
                await self.manager(interaction.guild.id, "clear")
                await interaction.response.edit_message(embed=embed, view=self)
                await interaction.guild.voice_client.disconnect()
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)

class queueButtons(discord.ui.View):
    def __init__(self, manager):
        super().__init__()
        self.lastButtonPressed = None
        self.manager = manager
        self.repeatEmojis = {0: "🚫", 1: "🔂", 2: "🔁"}
        self.repeatLabels = {0: "No Repeat", 1: "Repeat One", 2: "Repeat All"}
        self.currentRepeat = 2
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey, emoji="⏮️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            voiceClient.stop()
            await self.manager(interaction.guild.id, command="previous", ignoreNext=True)
            await interaction.response.edit_message(view=self)
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray, emoji="⏭️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            voiceClient.stop()
            await self.manager(interaction.guild.id, command="next", ignoreNext=True)
            await interaction.response.edit_message(view=self)
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)
    
    @discord.ui.button(label="Repeat All", style=discord.ButtonStyle.gray, emoji="🔁")
    async def repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        voiceClient = interaction.guild.voice_client
        if voiceClient:
            await self.manager(interaction.guild.id, command="repeat")
            repeatNumber = await self.manager(interaction.guild.id, "getRepeat")
            button.emoji = self.repeatEmojis[repeatNumber]
            button.label = self.repeatLabels[repeatNumber]
            await interaction.response.edit_message(view=self)
        else:
            embed = discord.Embed(title="Music Player", description="Not in voice chat", color=0x00ff00)
            await interaction.response.edit_message(embed=embed)

class musicPlayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.downloadQueue = []
        self.aviableSongFiles = [i for i in os.listdir(rf".\ytData") if i.endswith(".webm")]
        self.queues = {}

        self.autoplay.start()
        self.downloadAudio.start()
    
    class track(object):
        def __init__(self, YouTubeID, YouTubeObject, title, duration):
            self.YouTubeID = YouTubeID
            self.YouTubeObject = YouTubeObject
            self.title = title
            self.duration = duration
    
    class queue(object):
        def __init__(self, guildID):
            self.guildID = guildID
            self.queue = []
            self.position = 0
            self.repeat = 2 # 0 - off, 1 - repeat one, 2 - repeat all
            self.ignoreNext = True
            self.canPlay = True

        def __iter__(self): return self.queue
        def __len__(self): return len(self.queue)

        def append(self, track):
            self.queue.append(track)
            self.canPlay = True
        def clear(self): self.queue = []
        def pop(self, track): self.queue.pop(track)
        def getCurrentTrack(self):
            if self.position >= len(self.queue):
                if self.repeat == 0: self.canPlay = False
                if self.repeat == 2: self.position = 0; self.canPlay = True
                return None
            return self.queue[self.position]

        def next(self):
            if self.ignoreNext: self.ignoreNext = False
            elif self.repeat == 1: self.canPlay = True
            elif self.position >= len(self.queue):
                if self.repeat == 0: self.canPlay = False
                if self.repeat == 2: self.position = 0; self.canPlay = True
            else:
                self.position += 1
                self.canPlay = True
        
        def previous(self, ignoreNext):
            self.ignoreNext = ignoreNext
            if self.repeat == 1: pass
            elif self.position <= 0:
                if self.repeat == 0: self.canPlay = False
                if self.repeat == 2: self.position = len(self.queue) - 1
            else:
                self.position -= 1
                self.canPlay = True
        
        def repeatCycle(self, repeat):
            if repeat in (0, 1, 2): self.repeat = repeat
            else: self.repeat = 0 if self.repeat == 2 else self.repeat + 1

    async def queueManager(self, guildID: int, command: str, trackID: str=None, track: track=None, repeat: int=None, ignoreNext: bool=False):
        if guildID not in self.queues: self.queues[guildID] = self.queue(guildID)
        if command == "get": return self.queues[guildID].getCurrentTrack()
        elif command == "add": self.queues[guildID].append(self.track(*self.getYouTubeVideoData(trackID)))
        elif command == "clear":
            self.queues[guildID].clear()
            self.queues[guildID].position = 0
        elif command == "remove": self.queues[guildID].pop(track)
        elif command == "next": self.queues[guildID].next()
        elif command == "previous": self.queues[guildID].previous(ignoreNext)
        elif command == "repeat": self.queues[guildID].repeatCycle(repeat)
        elif command == "getPosition": return self.queues[guildID].position
        elif command == "getRepeat": return self.queues[guildID].repeat
        else: pass
    
    def check_link(self, data):
        if "v=" in data:
            search = data.split("v=")
            return search[1]
        else:
            keyword = "+".join(data.split(" "))
            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + keyword)
        return re.findall(r"watch\?v=(\S{11})", html.read().decode())[0]

    def getYouTubeVideoData(self, videoID: str):
        failed = 0
        while failed < 5: 
            try:
                ytVideo = YouTube("https://www.youtube.com/watch?v=" + videoID)
                title = ytVideo.title
                duration = ytVideo.length
                return videoID, ytVideo, title, duration
            except:
                failed += 1
                time.sleep(1)
                continue
        return None, None, None, None

    @app_commands.command(name = "play", description = "Plays a song from Wrangler")
    @app_commands.describe(search="Search for song on YouTube")
    async def play(self, interaction, search: str):
        await interaction.response.defer()
        voiceClient = interaction.guild.voice_client
        if interaction.user.voice is None:
            await interaction.edit_original_response("You are not in a voice channel")
            return
        else:
            if voiceClient: embedDescription = f"Currently in {interaction.user.voice.channel.name}"
            else: embedDescription = f"Joined {interaction.user.voice.channel.name}"
            embed = discord.Embed(title="Music Player", description=embedDescription)
            await interaction.edit_original_response(embed=embed)
            if voiceClient is None: await interaction.user.voice.channel.connect()
            else: await voiceClient.move_to(interaction.user.voice.channel)
        
        if voiceClient:
            if voiceClient.is_playing() or voiceClient.is_paused():
                currentTrack = await self.queueManager(interaction.guild.id, "get")
                if currentTrack: title = currentTrack.title
                else: title = "Nothing"
                
            else:
                embed = discord.Embed(title="Music Player", description="Currently playing: Nothing", color=0x00ff00)
                await interaction.edit_original_response(embed=embed)
                return
        else:
            songLinkID = self.check_link(search)
            _, _, title, _ = self.getYouTubeVideoData(songLinkID)
            if title == None:
                interaction.edit_original_response("Failed to get video, try again later")
                return
        
        if voiceClient:
            if (voiceClient.is_playing() or voiceClient.is_paused()):
                embed = discord.Embed(title="Music Player", description=f"Added {title} to queue", color=0x00ff00)
                await interaction.edit_original_response(embed=embed)
            else:
                embed = discord.Embed(title="Music Player", description=f"Currently playing: {title} ", color=0x00ff00)
                await interaction.edit_original_response(embed=embed, view=playerButtons(self.queueManager))
        else:
            embed = discord.Embed(title="Music Player", description=f"Currently playing: {title} ", color=0x00ff00)
            await interaction.edit_original_response(embed=embed, view=playerButtons(self.queueManager))
        await self.queueManager(interaction.guild.id, "add", trackID=songLinkID)
        self.downloadQueue.append(songLinkID)

    @app_commands.command(name = "join", description = "Joins the voice channel you are currently in")
    async def join(self, interaction):
        if interaction.user.voice is None:
            await interaction.channel.send("You are not in a voice channel")
        else:
            if interaction.guild.voice_client is None: await interaction.user.voice.channel.connect()
            else: await interaction.guild.voice_client.move_to(interaction.user.voice.channel)
            await interaction.response.send_message(f"Joined {interaction.user.voice.channel.name}")
    
    @app_commands.command(name = "leave", description = "Leaves the voice channel")
    async def leave(self, interaction):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("I am not in a voice channel")
        else:
            await interaction.guild.voice_client.disconnect()
            self.queues.get(interaction.guild.id).clear()
            await interaction.response.send_message("Left voice channel")
    
    @app_commands.command(name="player", description="Shows the music player")
    async def player(self, interaction):
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("I am not in a voice channel")
            return
        else:
            if interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused():
                song = await self.queueManager(interaction.guild.id, "get")
                title = song.title
            else:
                await interaction.response.send_message("No song is currently playing")
                return
            embed = discord.Embed(title="Music Player", description=f"Currently playing: {title} ", color=0x00ff00)
            await interaction.response.send_message(embed=embed, view=playerButtons(self.queueManager))
    
    @app_commands.command(name = "queue", description = "Shows the current queue")
    async def queueCommand(self, interaction):
        await interaction.response.defer()
        if interaction.guild.id not in self.queues:
            await interaction.edit_original_response("No queue")
        else:
            if len(self.queues[interaction.guild.id]) == 0:
                await interaction.edit_original_response("No queue")
            else:
                embed = discord.Embed(title="Queue", color=0x00ff00)
                guildQueue = self.queues[interaction.guild.id].queue
                for trackCount, trackObject in enumerate(guildQueue):
                    if trackCount > 10: break
                    title, length = trackObject.title, trackObject.duration
                    fieldName = f"{trackCount+1}. {title}"
                    fieldValue = f"Duration: {length // 60}:{str(length % 60).zfill(2)}"
                    embed.add_field(name=fieldName, value=fieldValue, inline=False)
                await interaction.edit_original_response(embed=embed, view=queueButtons(self.queueManager))

    @tasks.loop(seconds=1)
    async def downloadAudio(self):
        if len(self.downloadQueue) > 0:
            url = self.downloadQueue[0]
            filePath = rf".\ytData\{url}.webm"
            if not os.path.isfile(filePath):
                try:
                    log.logInfo(f"Downloading {url}", "musicPlayer.download", end=" | ")
                    yt = YouTube("https://www.youtube.com/watch?v=" + url)
                    yt.streams.filter(only_audio=True, mime_type="audio/webm")[0].download(filename=filePath)
                    self.aviableSongFiles.append(f"{url}.webm")
                    self.downloadQueue.pop(0)
                    print(f"Downloaded {yt.title}")
                except:
                    print(f"{Fore.RED}{Style.BRIGHT}ERROR", end=f"{Style.RESET_ALL}")
            else:
                self.downloadQueue.pop(0)

    @tasks.loop(seconds=2)
    async def autoplay(self):
        for guildID in self.queues:
            if len(self.queues[guildID].queue) > 0:
                if self.queues[guildID].canPlay:
                    voiceClient = self.bot.get_guild(guildID).voice_client
                    if voiceClient:
                        if not voiceClient.is_playing() and not voiceClient.is_paused():
                            track = await self.queueManager(guildID, command="get")
                            if track == None: continue
                            while True:
                                if f"{track.YouTubeID}.webm" in self.aviableSongFiles: break
                                if track.YouTubeID not in self.downloadQueue: self.downloadQueue.append(track.YouTubeID)
                                await asyncio.sleep(0.5)
                            source = FFmpegOpusAudio(rf".\ytData\{track.YouTubeID}.webm")
                            if voiceClient.is_connected():
                                voiceClient.play(source, after=await self.queueManager(guildID, command="next"))

async def setup(bot):
    log.logInfo("Loading musicPlayer", "setup.cogs")
    await bot.add_cog(musicPlayer(bot))