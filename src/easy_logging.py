import sys
import logging
import tempfile
from datetime import datetime
from typing import Optional


def __to_print_string_value(value) -> str:
    """ Internal Use.
    値を文字列に変換する関数
    """
    if type(value) is str:
        return "'{}'".format(value)
    if type(value) is dict:
        return "{" + ", ".join(["{}=<{}>".format(k, type(v)) for k, v in value.items()]) + "}"
    if type(value) is list:
        return "[(len={})" +\
            " 0: {}".format(value[0]) if value else "" +\
            ", ..." if len(value) > 1 else "" + "]"
    return str(value)[:200]


def __func_logging(cls_, func):
    """ Internal Use.
    メンバ関数をラップするロギング関数
    """
    def wrapper(*args, **kwargs):
        arg_dict = {func.__code__.co_varnames[i]: args[i] for i in range(len(args))}
        arg_dict.update(kwargs)
        if func.__name__ == "__init__":
            if "self" in arg_dict:
                arg_dict["self"] = "<self>"
            elif "cls" in arg_dict:
                arg_dict["cls"] = "<cls>"

        args_str = ", ".join(["{}={}".format(k, __to_print_string_value(arg_dict[k]))
                              for k in func.__code__.co_varnames[:func.__code__.co_argcount]
                              if k in arg_dict])

        cls_.logger.log(cls_.__function_log_level,
                        "START  {}({})".format(func.__qualname__, args_str))

        retval = func(*args, **kwargs)

        args_str = ""
        cls_.logger.log(cls_.__function_log_level,
                        "FINISH {}(...) -> {}".format(func.__qualname__, retval))
        return retval
    return wrapper


def __handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger().exception("Exception has occured.", exc_info=(exc_type, exc_value, exc_traceback))


#######################################################################################################################
# Easy Logging
#######################################################################################################################


def easy_logging(cls_=None, *, function_trace: bool = False, function_log_level: int = logging.DEBUG):
    """ ログ出力を簡単に行えるようにするためのデコレータ

    Parameters:
        function_trace (bool):
            メンバ関数に対して開始と終了にログ出力を行うか.
            呼び出しが頻繁に起こる関数が存在するとパフォーマンスに影響が出ます.
        function_log_level (int):
            メンバ関数に対するログ出力レベル
    """
    def wrapper(cls__):
        assert hasattr(cls__, "__name__")  # USE FOR CLASS ONLY
        if not hasattr(cls__, "logger"):
            setattr(cls__, "logger", logging.getLogger(cls__.__name__))
        setattr(cls__, "__function_log_level", function_log_level)

        if function_trace:
            for func in dir(cls__):
                if func.startswith("__") and func.endswith("__") and func != "__init__":
                    continue  # skip __***__ (exclude __init__())

                if callable(getattr(cls__, func)) and hasattr(getattr(cls__, func), "__module__"):
                    if cls__.__module__ == getattr(cls__, func).__module__:
                        setattr(cls__, func, __func_logging(cls__, getattr(cls__, func)))
        return cls__

    if cls_ is None:
        return wrapper
    return wrapper(cls_)


def setupLogger(file_prefix: str,
                console_level: int = logging.INFO,
                temp_logfile_level: int = logging.DEBUG,
                console_dest_stream=sys.stderr,
                latest_logfile_path: Optional[str] = None,
                latest_logfile_level: int = logging.INFO,
                is_hook_exception: bool = True,
                format_str: str = '[%(levelname)-7s] %(asctime)s::<%(name)-20s> | %(message)s',
                target_logger_instance: logging.Logger = logging.getLogger()
                ) -> logging.Logger:
    """ ロガーの書式を設定する

    Arguments:
        file_prefix (str):
            ログファイルのプレフィックス名.
        console_dest_stream:
            コンソール出力先のストリーム.
        console_level (int):
            コンソール出力のログレベル.
        temp_logfile_level (int):
            ログファイル出力のログレベル.
        latest_logfile_path (str):
            上書きで書き出されるログのファイルパス. None指定で書き出さない.
        latest_logfile_level (int):
            上書きで更新されるログファイル出力のログレベル.
        is_hook_exception (bool):
            例外出力をフックし、ログに出力するか.
        format_str (str):
            フォーマット書式文字列
        target_logger_instance (logging.Logger)
            設定を行うロガーインスタンス. デフォルトはルート（全体）.

    Returns:
        logging.Logger:
            設定を施したロガーインスタンス
    """
    assert file_prefix, 'Invalid Argument: file_prefix'

    logger = target_logger_instance
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format_str)

    # stdout
    stdout_handler = logging.StreamHandler(console_dest_stream)
    stdout_handler.setLevel(console_level)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # file
    strnow = datetime.now().strftime("%Y%m%d%H%M%S")
    fname = tempfile.mktemp('.log', file_prefix + strnow + '-')
    print(':: Logging to ' + fname, file=sys.stderr)
    file_handler = logging.FileHandler(filename=fname, mode='w', encoding='utf-8')
    file_handler.setLevel(temp_logfile_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Overwrite
    if latest_logfile_path is not None:
        ovr_file_handler = logging.FileHandler(filename=latest_logfile_path, mode='w', encoding='utf-8')
        ovr_file_handler.setLevel(latest_logfile_level)
        ovr_file_handler.setFormatter(formatter)
        logger.addHandler(ovr_file_handler)

    # exception hook
    if is_hook_exception:
        sys.excepthook = __handle_exception

    return logger
