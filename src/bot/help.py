import discord
import argparse


def setup(subparser: argparse._SubParsersAction, dev: bool = False):
    parser = subparser.add_parser("+help", help="BOTヘルプを表示します", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", dest="help_on_help")
    parser.set_defaults(show_help=True)
    return parser


async def authenticate(args, client: discord.Client, message: discord.Message):
    pass


async def run(args, client, message: discord.Message):
    await message.channel.send("ヘルプのヘルプ…:thinking_face:\n"
                               + "もし何か困りごとがあれば、開発者の<@!462643174087720971>に聞いてみてね！")
