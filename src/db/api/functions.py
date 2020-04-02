
def getDBFilepath(guild_id: int) -> str:
    assert type(guild_id)
    return "db_" + str(guild_id) + ".db"
