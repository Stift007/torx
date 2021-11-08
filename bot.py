import asyncio
import discord
from discord.ext import commands
import youtube_dl
from discord_slash import SlashCommand,SlashContext
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option,create_choice

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

bot = commands.Bot(command_prefix="t$")
slash = SlashCommand(bot,sync_commands=True)

class Music(commands.Cog):
    def __init__(self,client):
        self.bot = client

    @cog_ext.cog_slash(name="join",description="Make the Bot join your Voice channel",guild_ids=[850480795185053746,888062030890823690])
    async def join(self,ctx:SlashContext):
        if not ctx.author.voice:
            return await ctx.send("You are not in a Voice Channel!",hidden=1)
        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

        await ctx.send(f"Joined {voice_channel.name}")

    @cog_ext.cog_slash(name="pause",description="Pause the song",guild_ids=[850480795185053746,888062030890823690])
    async def pause(self,ctx:SlashContext):
        if not ctx.author.voice:
            return await ctx.send("You are not in a Voice Channel!",hidden=1)
        ctx.voice_client.pause()
        await ctx.send("Paused! ⏸️")
        
    @cog_ext.cog_slash(name="resume",description="Resume the song",guild_ids=[850480795185053746,888062030890823690])
    async def resume(self,ctx:SlashContext):
        if not ctx.author.voice:
            return await ctx.send("You are not in a Voice Channel!",hidden=1)
        ctx.voice_client.resume()
        await ctx.send("Resumed! \:play_button:")


    @cog_ext.cog_slash(name="leave",description="Make the Bot leave your Voice channel",guild_ids=[850480795185053746,888062030890823690])
    async def leave(self,ctx:SlashContext):
        if not ctx.author.voice:
            return await ctx.send("You are not in a Voice Channel!",hidden=1)
        await ctx.voice_client.disconnect()

    @cog_ext.cog_slash(name="play",description="Make the Bot play music to your Voice channel",guild_ids=[850480795185053746,888062030890823690],options=[
        create_option(
            name="url",
            description="The YouTube Query",
            option_type=3,
            required=True
        )
    ])
    async def play(self,ctx:SlashContext,url):
        if not ctx.author.voice:
            return await ctx.send("You are not in a Voice Channel!",hidden=1)
        try:
            ctx.voice_client.stop()
        except:
            ...

        voice_channel = ctx.author.voice.channel
        if not ctx.voice_client:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)


        player = await YTDLSource.from_url(url, loop=self.bot.loop,stream=True)
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.add_cog(Music(bot))
bot.run("TOKEN")
