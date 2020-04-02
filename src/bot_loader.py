import os
import logging
import bot as bot_processors
import importlib

from client import VemtClient


class ModuleImportError(Exception):
    def __init__(self, message):
        super().__init__(message)


def loadBotProcessors() -> list:
    logger: logging.Logger = logging.getLogger("botLoader")
    ret = []

    for filename in os.listdir(os.path.join(os.path.dirname(__file__), "bot")):
        name, ext = os.path.splitext(os.path.basename(filename))
        if ext == ".py" and name not in ["__init__"]:
            importlib.import_module(f"bot.{name}")
            logger.info(f"Module {name} loaded.")

            # エラーチェック
            loaded_module = getattr(bot_processors, name)
            for need_function_name in ["setup", "authenticate", "run"]:
                if not hasattr(loaded_module, need_function_name):
                    raise ModuleImportError(f"There is no '{need_function_name}()' in module '{name}'.")

            ret.append(loaded_module)
    return ret


def reloadBotProcessor(module):
    logger: logging.Logger = logging.getLogger("botLoader")
    importlib.reload(module)
    logger.info(f"!!DEVELOPMENT MODE!! module '{module.__name__}' is reloaded.")
