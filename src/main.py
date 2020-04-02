import os
import argparse
import logging

from easy_logging import setupLogger
import bot_loader
import client
import config as server_config


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(os.path.join(__file__, "../"))))

    # TODO: ここに説明を書く
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default="config/discord_token.txt", type=str, help="Filepath of token file.")
    parser.add_argument("--dev", action="store_true", help="enable developing mode.")
    args = parser.parse_args()

    # setup logger
    logger = setupLogger(file_prefix="vemt",
                         console_level=logging.DEBUG if args.dev else logging.INFO,
                         temp_logfile_level=logging.DEBUG,
                         latest_logfile_path="latest.log")

    # suppress logger
    for logger_name in (
        "discord.client",
        "discord.gateway",
        "discord.http",
        "websockets.protocol",
        "asyncio"
    ):
        discord_logger = logging.getLogger(logger_name)
        discord_logger.setLevel(logging.WARNING)

    # load config
    try:
        server_config.loadConfig()
    except Exception as e:
        logger.critical("Failed to load config. " + str(e))
        exit(1)

    # setup processor
    modules = bot_loader.loadBotProcessors()
    for module in modules:
        client.VemtClient.addProcessor(module, args.dev)

    # load token
    token_str: str = ""
    with open(args.token, mode="r", encoding="utf-8") as token_f:
        token_str = token_f.readline().strip()

    # client instance
    vemt_client = client.VemtClient(args)
    vemt_client.run(token_str)
