import discord
import argparse
import logging
import subprocess
import os
from typing import List, Optional
import sqlite3

import exception
import config
from db import database
from db.api import registry


def setup(subparser: argparse._SubParsersAction, dev: bool = True):
    parser = subparser.add_parser("+init",
                                  help="Discordサーバーを初期化します",
                                  description="Discordサーバーにおいて、チャンネル、ロールなどを作成します。\n"
                                  + "このコマンドは、**サーバーのオーナーのみ**が発行することができます。")
    parser.add_argument("server_name", help="確認のためサーバー名を入力してください", type=str, default="")
    return parser


async def authenticate(args, client: discord.Client, message: discord.Message):
    if not message.guild:
        raise exception.InvalidChannelError("+initコマンドはサーバでのみ発行可能です")

    if message.guild.owner.id != message.author.id:
        raise exception.PermissionDeniedError("+initコマンドはサーバーのオーナーのみが発行可能です")


async def run(args, client, message: discord.Message):
    logger: logging.Logger = logging.getLogger("InitProcess")

    # 既に初期化されていないか
    try:
        if registry.isServerInitialized(message.guild.id):
            raise exception.VemtCommandError("このサーバーは既に初期化されています")
    except sqlite3.OperationalError:
        # DBが存在しない
        pass

    if message.guild.name != args.server_name:
        raise exception.VemtCommandError("サーバー名が一致していません")

    logger.info("Start to initialize discord server.")
    await message.channel.send('Discordサーバーを初期化します\n'
                               '初期化中はサーバー設定の変更や、別のコマンドの発行をしないでください')

    if not message.guild:
        raise exception.VemtCommandError("ギルドの取得に失敗しました")
    guild: discord.Guild = message.guild
    logger.debug("- Guild ID = %d", guild.id)

    # 予約済みのチャンネルがあるか
    current_channels: List[discord.TextChannel] = guild.channels
    def_channels: List[str] = [
        config.getConfig().categoryName.bot,
        config.getConfig().categoryName.contact,
        config.getConfig().channelName.botControl,
        config.getConfig().channelName.entry,
        config.getConfig().channelName.status,
        config.getConfig().channelName.query
    ]

    logger.debug("- Listup guild channels.")
    for ch in current_channels:
        logger.debug("-- %s (%d)", ch.name, ch.id)
        for dc in def_channels:
            if ch.name == dc:
                logger.error("Already exists reserved channel. Channel name = %s", ch.name)
                raise exception.VemtCommandError("既に予約された名前のチャンネルが存在します")

    # 予約済みのロールがあるか
    everyone_role: Optional[discord.Role] = None
    current_roles: List[discord.Role] = guild.roles
    def_roles: List[str] = [
        config.getConfig().roleName.botAdmin,
        config.getConfig().roleName.preExhibitor,
        config.getConfig().roleName.exhibitor,
        config.getConfig().roleName.manager
    ]
    logger.debug("- Listup guild roles.")
    for rl in current_roles:
        logger.debug("-- %s (%d)", rl.name, rl.id)
        for drl in def_roles:
            if rl.name == "@everyone":
                everyone_role = rl
            elif rl.name == drl:
                logger.error("Already exists reserved role. Role name = %s", rl.name)
                raise exception.VemtCommandError("既に予約された名前のロールが存在します")

    if not everyone_role:
        logger.error("Not found @everyone role.", rl.name)
        raise exception.VemtCommandError("@everyoneロールが見つかりません")

    # ニックネーム
    logger.debug("- Changing BOT nickname to VEMT.")
    await guild.me.edit(nick="VEMT")
    logger.info("- Changed BOT nickname to VEMT.")

    # ロールを作る
    logger.debug("- Creating roles.")
    bot_admin_role: discord.Role = await guild.create_role(name=config.getConfig().roleName.botAdmin,
                                                           hoist=True, mentionable=True,
                                                           colour=discord.Color(0x3498db))
    manager_role: discord.Role = await guild.create_role(name=config.getConfig().roleName.manager,
                                                         hoist=True, mentionable=True,
                                                         colour=discord.Color(0xe74c3c))
    exhibitor_role: discord.Role = await guild.create_role(name=config.getConfig().roleName.exhibitor,
                                                           hoist=True, mentionable=True,
                                                           colour=discord.Color(0x2ecc71))
    pre_exhibitor_role: discord.Role = await guild.create_role(name=config.getConfig().roleName.preExhibitor,
                                                               hoist=True, mentionable=True,
                                                               colour=discord.Color(0x208c4e))
    logger.info("- Created roles.")

    # カテゴリを作る
    logger.debug("- Creating categories.")
    bot_category: discord.CategoryChannel = await guild.create_category_channel(config.getConfig().categoryName.bot)
    contact_category: discord.CategoryChannel = await guild.create_category_channel(
        name=config.getConfig().categoryName.contact,
        overwrites={guild.default_role: discord.PermissionOverwrite(read_messages=False)})
    logger.info("- Created categories.")

    # チャンネルを作る
    # BOTの管理用チャンネル
    logger.debug("- Creating channels.")
    bot_manage_channel: discord.TextChannel = await guild.create_text_channel(
        name=config.getConfig().channelName.botControl,
        category=bot_category,
        topic="BOTの設定変更など、BOT管理を行うチャンネルです。`+config --help`でヘルプを表示します。",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            bot_admin_role: discord.PermissionOverwrite(read_messages=True)
        }
    )

    # 出展応募用チャンネル
    entry_channel: discord.TextChannel = await guild.create_text_channel(
        name=config.getConfig().channelName.entry,
        category=bot_category,
        topic="仮エントリーを申し込むためのチャンネルです。エントリー受付期間中、`+entry`で仮エントリーが可能です。",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(send_messages=False)
        }
    )

    # 情報問い合わせ用チャンネル
    query_channel: discord.TextChannel = await guild.create_text_channel(
        name=config.getConfig().channelName.query,
        category=bot_category,
        topic="様々な情報を取得することができます。運営専用チャンネルです。`+query --help`でヘルプを表示します。",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            manager_role: discord.PermissionOverwrite(read_messages=True)
        }
    )

    # ステータス確認用のチャンネル
    status_channel: discord.TextChannel = await guild.create_text_channel(
        name=config.getConfig().channelName.status,
        category=bot_category,
        topic="サーバーに関するステータス確認用のチャンネルです。",
        overwrites={
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
        }
    )
    logger.info("- Created channels.")

    # DBを作成
    db_proc = subprocess.Popen(
        "sqlite3 {} < {}".format(
            database.toDBFilepath(guild.id),
            os.path.abspath("src/db/scheme.sql")),
        shell=True)
    db_proc.wait()

    # サーバー固有のIDを記録する
    # Database
    registry.setupGuildIds(guild_id=guild.id,
                           category_bot_id=bot_category.id,
                           category_contact_id=contact_category.id,
                           channel_bot_control_id=bot_manage_channel.id,
                           channel_entry_id=entry_channel.id,
                           channel_status_id=status_channel.id,
                           channel_query_id=query_channel.id,
                           role_bot_admin_id=bot_admin_role.id,
                           role_pre_exhibitor_id=pre_exhibitor_role.id,
                           role_exhibitor_id=exhibitor_role.id,
                           role_manager_id=manager_role.id)

    await message.channel.send(
        "**成功** サーバーの初期化が完了しました\n" +
        "BOTコマンドについては、`+help`コマンドから参照することができます。（ただし<@&{}>か<@&{}>のみが発行可能です）\n".format(
            bot_admin_role.id, manager_role.id) +
        "質問の登録や期間設定などを<#{}>チャンネルで設定後、エントリーを開始してください".format(bot_manage_channel.id))
    logger.info("- Finished initializing guild. Guild : %s (%d)", guild.name, guild.id)
