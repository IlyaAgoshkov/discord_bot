import discord
from discord.ext import commands
from pytube import YouTube
import asyncio
from discord import Intents
from config import token

intents = Intents.default()
intents.members = True
intents.typing = False
intents.presences = False
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Добавляем глобальную переменную для хранения очередей
queues = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def play_song(ctx, url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            await ctx.send("Не удалось получить аудиопоток для этого видео!")
            return

        ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }

        audio_source = discord.FFmpegPCMAudio(stream.url, **ffmpeg_options)
        ctx.voice_client.play(audio_source, after=lambda e: check_queue(ctx))
        await ctx.send(f"Играет... {yt.title}")

    except Exception as e:
        print(f"Error in play command: {e}")
        await ctx.send("Произошла ошибка при попытке воспроизведения.")

def check_queue(ctx):
    if queues.get(ctx.guild.id) and len(queues[ctx.guild.id]) > 0:
        next_song = queues[ctx.guild.id].pop(0)
        asyncio.run_coroutine_threadsafe(play_song(ctx, next_song), bot.loop)

@bot.command()
async def play(ctx, url):
    if not ctx.author.voice:
        await ctx.send("Вы не находитесь в голосовом канале!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    if not ctx.voice_client.is_playing():
        await play_song(ctx, url)
    else:
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.send(f"Добавлено в очередь: {url}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Остановлено!")
    else:
        await ctx.send("Сейчас ничего не играет!")

@bot.command()
async def queue(ctx):
    if ctx.guild.id in queues:
        queue_list = "\n".join(queues[ctx.guild.id])
        await ctx.send(f"Следующие треки:\n{queue_list}")
    else:
        await ctx.send("В очереди нет песни!")

bot.run(token)
