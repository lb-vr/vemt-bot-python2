import discord
import argparse

from typing import List

import config
import exception
from db.api import entries


def setup(subparser: argparse._SubParsersAction, dev: bool = True):
    if dev:
        parser = subparser.add_parser("+reset", help="【BOT開発専用】Discordサーバーをもとの状態に戻します", add_help=False)
        return parser


async def authenticate(args, client: discord.Client, message: discord.Message):
    if message.guild is None:
        raise exception.InvalidChannelError("+resetコマンドはサーバーのテキストチャンネルでのみ実行可能です")
    if message.guild.owner.id != message.author.id:
        raise exception.PermissionDeniedError("+resetコマンドはサーバーのオーナーのみが発行可能です")


async def run(args, client, message: discord.Message):
    await message.channel.send('Discordサーバーをもとに戻しています')

    if not message.guild:
        raise exception.VemtCommandError("ギルドの取得に失敗しました", detail=f"message.guild={str(message.guild)}")

    guild: discord.Guild = message.guild

    # 作成済みのチャンネルを削除
    # あえて名前一致で削除する
    current_channels: List[discord.TextChannel] = guild.channels
    def_channels: List[str] = [
        config.getConfig().categoryName.bot,
        config.getConfig().categoryName.contact,
        config.getConfig().channelName.botControl,
        config.getConfig().channelName.entry,
        config.getConfig().channelName.status,
        config.getConfig().channelName.query
    ]

    for ch in current_channels:
        for dc in def_channels:
            if ch.name == dc:
                await ch.delete()

    # コンタクトチャンネル
    entries_list = entries.getAll(guild.id)
    for ch in current_channels:
        for entry in entries_list:
            if ch.id == entry.contactChannelId:
                await ch.delete()

    # 作成済みのロールを削除
    current_roles: List[discord.Role] = guild.roles
    def_roles: List[str] = [
        config.getConfig().roleName.botAdmin,
        config.getConfig().roleName.preExhibitor,
        config.getConfig().roleName.exhibitor,
        config.getConfig().roleName.manager
    ]

    for rl in current_roles:
        for drl in def_roles:
            if rl.name == drl:
                await rl.delete()

    # ニックネーム戻す
    await guild.me.edit(nick=None)
    await message.channel.send("**成功** サーバーをもとに戻しました\n")
