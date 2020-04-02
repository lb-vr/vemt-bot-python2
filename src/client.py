import discord
import logging
import shlex

import exception
import bot_loader
from classes import VemtArgumentParser


class VemtClient(discord.Client):
    __parser: VemtArgumentParser = VemtArgumentParser(
        prog="",
        usage="VEMT",
        description="VEMT-BOTは、\"+\"文字を先頭に付けたコマンドをもとに処理を行います。\n"
        + "Discordのメッセージとしてコマンドを入力し、送信することで解釈を行います。 \n"
        + "コマンドによっては、権限によって制限されたものや、チャンネルが決まっています。\n",
        epilog="それぞれのコマンドについて詳しく知るには、`+<コマンド> --help`で見ることが可能です。",
        add_help=False)
    __subparser = None
    __processor_parsers: dict = {}

    @classmethod
    def addProcessor(cls, bot_module, dev: bool = False):
        logger = logging.getLogger("VemtClient")
        if not cls.__subparser:
            cls.__subparser = cls.__parser.add_subparsers(parser_class=VemtArgumentParser)

        parser = bot_module.setup(subparser=cls.__subparser, dev=dev)
        if parser is not None:
            parser.set_defaults(handler=bot_module)
            cls.__processor_parsers[bot_module.__name__] = parser
            logger.debug("add bot processor: %s", bot_module.__name__)

    def __init__(self, args, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.__system_args = args

    async def on_ready(self):
        logger = logging.getLogger()
        logger.info('Logged on as {0}!'.format(self.user))

    async def on_message(self, message: discord.Message):
        logger = logging.getLogger()

        if not message.author.bot and message.content.startswith("+"):
            logger.debug('Message from {0.author} ({0.author.id}): {0.content}'.format(message))
            logger.debug('Guild: {0.guild.id}'.format(message))
            try:
                args = VemtClient.__parser.parse_args(shlex.split(message.content))
                logger.debug("arguments : %s", args)

                if hasattr(args, "handler") and args.handler.__name__ in VemtClient.__processor_parsers:
                    bot_module = args.handler

                    if self.__system_args.dev:
                        bot_loader.reloadBotProcessor(bot_module)

                    await bot_module.authenticate(args, self, message)

                    if hasattr(args, "help") and args.help:
                        await message.channel.send(VemtClient.__processor_parsers[bot_module.__name__].format_help())
                    else:
                        if hasattr(args, "show_help") and not args.help_on_help:
                            VemtClient.__parser.print_help()
                        else:
                            await bot_module.run(args, self, message)
                else:
                    raise exception.CommandNotFoundError("そのようなコマンドは存在しません")

            except exception.ShowHelp as e:
                # コマンドのヘルプ
                await message.channel.send(e.help_str)

            except exception.ArgError as e:
                await message.channel.send(":x: " + str(e))

            except SystemExit:
                logger.debug("stopped to exit system.")

            except exception.PermissionDeniedError:
                await message.channel.send(":x: **失敗** このコマンドを実行する権限がありません")

            except exception.VemtCommandError as e:
                await message.channel.send(":x: **失敗** " + str(e))
