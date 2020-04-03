import datetime
from typing import Optional, Tuple
from db.database import Database, toDBFilepath


def getInt(guild_id: int, key: str, default_value: int = None) -> Optional[int]:
    with Database(database=toDBFilepath(guild_id)) as db:
        ret = db.select("registry_int", columns=["itemvalue"], condition={"title": key})
        if ret:
            return ret[0]["itemvalue"]
        return default_value


def setInt(guild_id: int, key: str, value: int):
    with Database(database=toDBFilepath(guild_id)) as db:
        db.insert("registry_int", candidate={"title": key, "itemvalue": value})


def getDatetime(guild_id: int, key: str, default_value: datetime.datetime = None) -> Optional[datetime.datetime]:
    with Database(database=toDBFilepath(guild_id)) as db:
        ret = db.select("registry_datetime", columns=["itemvalue"], condition={"title": key})
        if ret:
            return ret[0]["itemvalue"]
        return default_value


def isServerInitialized(guild_id: int) -> bool:
    ret = getDatetime(guild_id, "guild.setup", None)
    return ret is not None


def setupGuildIds(guild_id: int,
                  category_bot_id: int,
                  category_contact_id: int,
                  channel_bot_control_id: int,
                  channel_entry_id: int,
                  channel_status_id: int,
                  channel_query_id: int,
                  role_bot_admin_id: int,
                  role_exhibitor_id: int,
                  role_pre_exhibitor_id: int,
                  role_manager_id: int):

    with Database(database=toDBFilepath(guild_id), isolation_level="EXCLUSIVE") as db:
        db.insert("registry_int", candidate={"title": "guild.id", "itemvalue": guild_id})
        db.insert("registry_int", candidate={"title": "category.bot.id", "itemvalue": category_bot_id})
        db.insert("registry_int", candidate={"title": "category.contact.id", "itemvalue": category_contact_id})
        db.insert("registry_int", candidate={"title": "channel.bot-control.id", "itemvalue": channel_bot_control_id})
        db.insert("registry_int", candidate={"title": "channel.entry.id", "itemvalue": channel_entry_id})
        db.insert("registry_int", candidate={"title": "channel.status.id", "itemvalue": channel_status_id})
        db.insert("registry_int", candidate={"title": "channel.query.id", "itemvalue": channel_query_id})
        db.insert("registry_int", candidate={"title": "role.bot-admin.id", "itemvalue": role_bot_admin_id})
        db.insert("registry_int", candidate={"title": "role.pre-exhibitor.id", "itemvalue": role_pre_exhibitor_id})
        db.insert("registry_int", candidate={"title": "role.exhibitor.id", "itemvalue": role_exhibitor_id})
        db.insert("registry_int", candidate={"title": "role.manager.id", "itemvalue": role_manager_id})
        db.insert("registry_datetime", candidate={"title": "guild.setup", "itemvalue": datetime.datetime.now()})

        db.commit()


class Ids:
    def __init__(self, kwargs):
        self.categoryBot = kwargs["category.bot.id"]
        self.categoryContact = kwargs["category.contact.id"]
        self.channelBotControl = kwargs["category.bot.id"]
        self.channelEntry = kwargs["channel.entry.id"]
        self.channelStatus = kwargs["channel.status.id"]
        self.channelQuery = kwargs["channel.query.id"]
        self.roleBotAdmin = kwargs["role.bot-admin.id"]
        self.rolePreExhibitor = kwargs["role.pre-exhibitor.id"]
        self.roleExhibitor = kwargs["role.exhibitor.id"]
        self.roleManager = kwargs["role.manager.id"]


def getGuildIds(guild_id) -> Ids:
    with Database(database=toDBFilepath(guild_id)) as db:
        results = db.search(table="registry_int",
                            columns=["title", "itemvalue"],
                            condition={"title": "%.id"})

        ret = Ids({r["title"]: r["itemvalue"] for r in results})
        return ret


def getPeriod(guild_id: int, key: str) -> Optional[Tuple[datetime.datetime, datetime.datetime]]:
    with Database(database=toDBFilepath(guild_id)) as db:
        ret_since = db.select("registry_datetime", columns=["itemvalue"], condition={"title": f"{key}.since"})
        ret_until = db.select("registry_datetime", columns=["itemvalue"], condition={"title": f"{key}.until"})
        if ret_since and ret_until:
            return (ret_since[0], ret_until[0])
        return None


def getEntryPeriod(guild_id: int) -> Optional[Tuple[datetime.datetime, datetime.datetime]]:
    return getPeriod(guild_id=guild_id, key="schedule.limitation.entry")
