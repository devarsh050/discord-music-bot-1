import asyncio
import discord
import os
from discord.ext import commands
from glob import glob
from pathlib import Path

bot = commands.Bot(command_prefix='!')

BOT_TOKEN = 'NTI0NTU5ODQ2MjQ3MjM1NTk0.Dvp2Dg.zNPhkoF3AfVkvmmWuh1AuT4zJu8'
MUSIC_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/music'

REQUEST_PATH = 'path'
REQUEST_TYPE = 'request_type'
REQUEST_TYPE_FILE = 'file'
REQUEST_TYPE_URL = 'youtube'


class MusicBot:
    def __init__(self):
        self.voice = None
        self.player = None
        self.volume = 1
        self.player_queue = []
        self.queue_position = 0
        self.music_list = []

    def set_voice_channel(self, voice_channel):
        self.voice = voice_channel


bot_object = MusicBot()
loop_event = asyncio.get_event_loop()


def is_not_joined_voice_channel(voice) -> bool:
    return voice is None


def update_bot_object_music_list():
    bot_object.music_list = glob(MUSIC_FOLDER + '/*.mp3')


@bot.event
async def on_ready():
    """
    コード起動時

    :return:
    """
    update_bot_object_music_list()
    print('起動！')


@bot.command(pass_context=True)
async def play(ctx, request=None):
    """
    音楽の再生及びキューへ

    :param ctx:
    :param request:
    :return:
    """
    if is_not_joined_voice_channel(ctx.author.voice):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    try:
        request = int(request)
    except ValueError:
        await bot.send_message(ctx.message.channel, '再生番号は数字で入力してください')
        return
    except TypeError:
        pass
    if bot_object.voice is None:
        bot_object.voice = await bot.join_voice_channel(ctx.message.author.voice_channel)
    play_content = {REQUEST_TYPE: REQUEST_TYPE_FILE, REQUEST_PATH: bot_object.music_list[request]}
    if bot_object.player is None:
        await player_start(play_content)
    else:
        if bot_object.player.is_playing():
            bot_object.player_queue.append(play_content)
        else:
            await player_start(play_content)


@bot.command(pass_context=True)
async def uplay(ctx, url=None):
    if is_not_joined_voice_channel(ctx.message):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    if url is None:
        await bot.send_message(ctx.message.channel, 'youtubeのURLを指定してください！！')
        return
    if bot_object.voice is None:
        bot_object.voice = await bot.join_voice_channel(ctx.message.author.voice_channel)
    play_content = {REQUEST_TYPE: REQUEST_TYPE_URL, REQUEST_PATH: url}
    if bot_object.player is None:
        await player_start(play_content)
    else:
        if bot_object.player.is_playing():
            bot_object.player_queue.append(play_content)
        else:
            await player_start(play_content)


async def player_start(play_content: dict):
    play_type = play_content[REQUEST_TYPE]
    play_path = play_content[REQUEST_PATH]
    if play_type == REQUEST_TYPE_FILE:
        bot_object.player = await bot_object.voice.create_ffmpeg_player(play_path)
    elif play_type == REQUEST_TYPE_URL:
        bot_object.player = await bot_object.voice.create_ytdl_player(play_path)
    set_player_volume()
    bot_object.player.start()
    await asyncio.ensure_future(is_check_now_play())


async def is_check_now_play():
    """
    playerが再生中か判定のループ
    再生状態でなくなった時、キューの確認メソッドを呼び出す
    :return:
    """
    if not bot_object.player.is_playing():
        await play_next()
    else:
        await asyncio.sleep(1)
        await asyncio.ensure_future(is_check_now_play())


async def play_next():
    if len(bot_object.player_queue) > 0:
        play_content = bot_object.player_queue.pop(0)
        await player_start(play_content)


# ローカルの音楽リスト
@bot.command(pass_context=True)
async def list(ctx, search_word=None):
    """
    ローカルの音楽リストを出力

    :param ctx:
    :return:
    """
    if is_not_joined_voice_channel(ctx.message):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    embed = discord.Embed(title='Music List', description="音楽ファイルリスト", color=0xeee657)
    for i, music in enumerate(bot_object.music_list):
        music_name = Path(music).stem
        embed.add_field(name=str(i) + '\t:\t' + music_name, value='\u200b', inline=False)
    await bot.send_message(ctx.message.channel, embed=embed)


@bot.command(pass_context=True)
async def volume(ctx, request=0):
    if is_not_joined_voice_channel(ctx.message):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    try:
        request = int(request)
    except ValueError:
        await bot.send_message(ctx.message.channel, '音量は数値で入力してください')
        return
    except TypeError:
        pass
    bot_object.volume = request
    set_player_volume()


def set_player_volume():
    bot_object.player.volume = bot_object.volume / 100


@bot.command(pass_context=True)
async def queue(ctx):
    """
    キューに入っている再生リストの表示

    :param ctx:
    :return:
    """
    if is_not_joined_voice_channel(ctx.message):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    embed = discord.Embed(title="再生待ちリスト", description="現在の再生待ちリスト")
    for i, music_path in enumerate(bot_object.player_queue):
        embed.add_field(name=str(i) + '\t:\t' + Path(music_path).name, value='\u200b',
                        inline=False)
    await bot.send_message(ctx.message.channel, embed=embed)


@bot.command(pass_context=True)
async def all_play(ctx):
    """
    フォルダに格納されている音楽をすべて再生

    :param ctx:
    :return:
    """
    if is_not_joined_voice_channel(ctx.message):
        await bot.send_message(ctx.message.channel, 'ボイスチャンネルに参加した上で実行してください！！')
        return
    for music_path in bot_object.music_list:
        bot_object.player_queue.append(music_path)


bot.run(BOT_TOKEN)
