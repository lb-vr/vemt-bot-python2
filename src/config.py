import json
from typing import Optional, Dict


class ConfigTypeError(Exception):
    def __init__(self, arg_key, arg_val, typ):
        super().__init__(f"Config Error: '{arg_key}' value must be '{str(typ)}', actually '{str(type(arg_val))}'")

    @classmethod
    def checkAndGet(cls, args, key, default, typ=str):
        val = args.get(key, default)
        if type(val) is not typ:
            raise cls(key, val, typ)
        return val


class CategoryName:
    def __init__(self, **args):
        self.__bot: str = ConfigTypeError.checkAndGet(args, "bot", "bot")
        self.__contact: str = ConfigTypeError.checkAndGet(args, "contact", "contact")

    @property
    def bot(self) -> str:
        return self.__bot

    @property
    def contact(self) -> str:
        return self.__contact


class ChannelName:
    def __init__(self, **args):
        self.__bot_control: str = ConfigTypeError.checkAndGet(args, "bot_control", "bot-control")
        self.__entry: str = ConfigTypeError.checkAndGet(args, "entry", "entry")
        self.__status: str = ConfigTypeError.checkAndGet(args, "status", "status")
        self.__query: str = ConfigTypeError.checkAndGet(args, "query", "query")

    @property
    def botControl(self) -> str:
        return self.__bot_control

    @property
    def entry(self) -> str:
        return self.__entry

    @property
    def status(self) -> str:
        return self.__status

    @property
    def query(self) -> str:
        return self.__query


class RoleName:
    def __init__(self, **args):
        self.__bot_admin = ConfigTypeError.checkAndGet(args, "bot_admin", "BOT-Admin")
        self.__exhibitor = ConfigTypeError.checkAndGet(args, "exhibitor", "Exhibitor")
        self.__manager = ConfigTypeError.checkAndGet(args, "manager", "Manager")

    @property
    def botAdmin(self) -> str:
        return self.__bot_admin

    @property
    def exhibitor(self) -> str:
        return self.__exhibitor

    @property
    def manager(self) -> str:
        return self.__manager


class Config:
    def __init__(self, **args):
        self.__category_name: CategoryName = CategoryName(**ConfigTypeError.checkAndGet(args, "categories", {}, dict))
        self.__channel_name: ChannelName = ChannelName(**ConfigTypeError.checkAndGet(args, "channels", {}, dict))
        self.__role_name: RoleName = RoleName(**ConfigTypeError.checkAndGet(args, "roles", {}, dict))

    @property
    def categoryName(self) -> CategoryName:
        return self.__category_name

    @property
    def channelName(self) -> ChannelName:
        return self.__channel_name

    @property
    def roleName(self) -> RoleName:
        return self.__role_name


_configInstance = None


def loadConfig():
    global _configInstance
    if _configInstance is None:
        with open("config/config.json", mode="r", encoding="utf-8") as f:
            jdict = json.load(f)
            _configInstance = Config(**jdict)


def getConfig() -> Config:
    assert _configInstance is not None
    return _configInstance
