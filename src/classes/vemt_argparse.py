import argparse
import exception

_replace_map = {
    "usage:": "使い方:",
    "positional arguments:": "引数:",
    "optional arguments:": "省略可能な引数:",
    "show this help message and exit": "このヘルプを表示します"
}


class VemtArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise exception.ArgError(message)

    def _print_message(self, message: str, file=None):
        if message:
            for k, v in _replace_map.items():
                message = message.replace(k, v)
            raise exception.ShowHelp(message)
