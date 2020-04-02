import logging


class VemtCommandError(Exception):
    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        logger.warning(f"コマンドエラー: {message}")
        for k, v in kwargs:
            try:
                logger.warning(" --- {} = {}".format(k, str(v).replace("\n", "\\n")))
            except Exception as e:
                logger.warning(f" --- {k} = <<Failed to print. {e} ({str(type(e))})>>")


# VemtArgumentParser

class ArgError(VemtCommandError):
    __translate = {
        "unrecognized arguments:": "不明な引数が指定されました:",
        "invalid choice:": "不正な引数選択です:",
        "choose from": "次のうちから選んでください:",
        "the following arguments are required:": "次の引数は必ず指定してください:"
    }

    def __init__(self, message):
        for k, v in ArgError.__translate.items():
            message = message.replace(k, v)
        super().__init__(message)

# これだけ例外でException継承


class ShowHelp(Exception):
    def __init__(self, help_str: str):
        super().__init__("It's ok.")
        self.__help_str: str = help_str

    @property
    def help_str(self) -> str:
        return self.__help_str


# Client

class CommandNotFoundError(VemtCommandError):
    pass


class PermissionDeniedError(VemtCommandError):
    def __init__(self, message="このコマンドを実行する権限がありません", **kwargs):
        super().__init__(message, **kwargs)
    pass


class InvalidChannelError(VemtCommandError):
    pass
