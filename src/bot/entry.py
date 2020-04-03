import discord
import argparse
import logging
import datetime

from typing import NoReturn, List, Tuple, Optional

import exception
from db.api import registry, entries


def setup(subparser: argparse._SubParsersAction, dev: bool = False):
    parser = subparser.add_parser("+entry",
                                  help="エントリーを行います",
                                  description="出展エントリーを行います。\n"
                                  + "このコマンドは、エントリー期間のみ、イベントに出展予定の方が使用します。")
    return parser


async def authenticate(args, client: discord.Client, message: discord.Message):
    # サーバーは初期化済みか
    if not registry.isServerInitialized(message.guild.id):
        raise exception.VemtCommandError("このサーバーは初期化されていません")

    if not message.guild:
        raise exception.InvalidChannelError("+entryコマンドはサーバでのみ発行可能です")

    if message.guild.owner.id != message.author.id:
        raise exception.PermissionDeniedError("+entryコマンドはサーバーのオーナーのみが発行可能です")


async def run(args, client, message: discord.Message):
    logger: logging.Logger = logging.getLogger("EntryProcess")

    if not message.guild:
        raise exception.VemtCommandError("ギルドの取得に失敗しました")
    guild: discord.Guild = message.guild
    logger.debug("- Guild ID = %d", guild.id)

    # 既にエントリーしていない？
    entried_user = entries.getFromDiscordId(guild.id, message.author.id)
    if entried_user:
        raise exception.VemtCommandError("既にエントリーが完了しています")

    # エントリー期間か？
    now = datetime.datetime.now()
    entry_period = registry.getEntryPeriod(guild.id)
    if entry_period is None:
        raise exception.VemtCommandError("現在、エントリーは受け付けておりません")
    if not (entry_period[0] < now < entry_period[1]):
        raise exception.VemtCommandError("現在、エントリーは受け付けておりません")

    # エントリーチャンネルか
    ids = registry.getGuildIds(guild.id)
    if message.channel.id != ids.channelEntry:
        raise exception.VemtCommandError("エントリーは<#{}>チャンネルのみで受け付けています".format(ids.channelEntry))

    # 役職「PreExhibitor」を与える
    pre_exhibitor_role = message.guild.get_role(ids.rolePreExhibitor)
    await message.author.add_roles(pre_exhibitor_role)

    # 役職「Manager」を取得
    manager_role = message.guild.get_role(ids.roleManager)

    # Contactカテゴリ取得
    contact_category = message.guild.get_channel(ids.categoryContact)

    # チャンネルを作成
    channel_name = message.author.nick if message.author.nick is not None else str(message.author.name)
    contact_channel = await message.guild.create_text_channel(
        name="{}-{}".format(channel_name, message.author.id),
        overwrites={
            message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            message.author: discord.PermissionOverwrite(read_messages=True),
            manager_role: discord.PermissionOverwrite(read_messages=True)
        },
        category=contact_category
    )

    new_user: entries.Entry = entries.entry(guild.id,
                                            discord_user_id=message.author.id,
                                            channel_id=contact_channel.id)
    logger.info("Entried! User=%s", new_user)

    # チャンネルにテキストチャット
    await contact_channel.send("<@!{}>さん、こちらがコンタクトチャンネルです。".format(message.author.id))

    # レス
    await message.add_reaction("✅")
    await message.channel.send(
        "<@!{}>さん、仮エントリーを受け付けました。CONTACTチャンネルにて、手続きを続行してください。".format(message.author.id))
