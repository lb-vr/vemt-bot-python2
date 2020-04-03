import discord
import argparse
import exception


def setup(subparser: argparse._SubParsersAction, dev=False):
    if dev:
        parser = subparser.add_parser("+exit",
                                      help="【BOT開発専用】BOTを終了します",
                                      add_help=False)
        return parser
    return None


async def authenticate(args, client: discord.Client, message: discord.Message):
    if not message.guild:
        raise exception.InvalidChannelError("+exitコマンドはサーバでのみ発行可能です")

    if message.guild.owner.id != message.author.id:
        raise exception.PermissionDeniedError("+exitコマンドはサーバーのオーナーのみが発行可能です")


async def run(args, client: discord.Client, message: discord.Message):
    await message.channel.send('OK, See you. ')
    await client.close()
