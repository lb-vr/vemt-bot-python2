import datetime
from typing import Optional, List
from db.database import Database, toDBFilepath


class Entry:
    def __init__(self, result: dict):
        super().__init__()
        self.__data: dict = result

    @property
    def entryId(self) -> int:
        return self.__data["id"]

    @property
    def discordUserId(self) -> int:
        return self.__data["discord_user_id"]

    @property
    def contactChannelId(self) -> int:
        return self.__data["contact_channel_id"]

    @property
    def created(self) -> datetime.datetime:
        raise NotImplementedError("時刻のフォーマットが分からん" + str(self.__data["created_at"]))

    @property
    def updated(self) -> datetime.datetime:
        raise NotImplementedError("時刻のフォーマットが分からん" + str(self.__data["updated_at"]))


def getAllEntries(guild_id: int) -> List[Entry]:
    with Database(toDBFilepath(guild_id)) as db:
        return [Entry(result) for result in db.select("entries")]
