import sqlite3
import logging

from typing import Optional, Dict, Any, List


class DatabaseError(Exception):
    pass


def toDBFilepath(guild_id: int) -> str:
    assert type(guild_id)
    return "db_" + str(guild_id) + ".db"


class Database:

    def __init__(self, database: str, isolation_level: Optional[str] = None):
        """ データベースオブジェクトを初期化する。

        Args:
            database (str): データベースのファイルアドレス
            isolation_level (str): トランザクションを構築するか. DEFERRED / IMMEDIATE / EXCLUSIVE / None
        """
        assert type(database), "invalid argument type, database=" + database
        assert database != ""
        self.__database: str = database
        self.__isolation_level: Optional[str] = isolation_level
        self.__connection: Optional[sqlite3.Connection] = None
        self.__logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    def __enter__(self):
        self.__connection = sqlite3.connect(
            self.__database,
            isolation_level=self.__isolation_level,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.__connection.row_factory = sqlite3.Row
        sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if exception_value:
            self.__connection.rollback()
        self.__connection.close()
        self.__connection = None

    def commit(self):
        """ データベースへの変更をコミットする
        """
        self.__connection.commit()

    @property
    def logger(self) -> logging.Logger:
        """ 基底で用意したロガーを取得する
        Returns:
            logging.Logger: ロガーインスタンス
        """
        return self.__logger

    @property
    def database(self) -> str:
        """ データベースのファイルパスを取得する
        Returns:
            str: データベースへのファイルパス
        """
        return self.__database

    @property
    def connection(self) -> Optional[sqlite3.Connection]:
        """ データベースコネクションを取得する

        データベースコネクションは、コンストラクタにて取得される

        Returns:
            sqlite3.Connection: データベースへのコネクション
        """
        return self.__connection

    def __execute(self, sql_text: str, bindee: Optional[list] = None, request_last_id: bool = False) -> list:
        """ データベースに対してsqlを実行する

        Args:
            sql_text (str): SQLクエリ
            bindee (Optional[list]): バインドする値. 空リストはAssertionError

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        assert type(sql_text) is str
        assert type(bindee) is list if bindee is not None else True
        assert len(bindee) > 0 if bindee is not None else True

        ret: list = []
        try:
            if self.connection is None:
                raise DatabaseError("No Connection.")
            c = self.connection.cursor()
            if bindee is not None:
                self.logger.debug("Execute < %s [values=%s]", sql_text, ",".join([str(d) for d in bindee]))
                c.execute(sql_text, tuple(bindee))
            else:
                self.logger.debug("Execute < %s [With no value]", sql_text)
                c.execute(sql_text)

            ret = c.fetchall()  # Result Fetch
            self.logger.debug("Fetched > %d results.", len(ret))

            if request_last_id:
                ret.insert(0, c.lastrowid)

            c.close()

        except sqlite3.Error as e:
            self.logger.warning("Failed  > Error has occured. {}: {}".format(type(e), e))
            raise e  # Re-throw
        return ret

    def select(self, table: str, columns: List[str] = ["*"], condition: Dict[str, Any] = {}) -> list:
        """ データベースからデータを取得する基礎関数

        Args:
            table(str): テーブル名
            columns(List[str]): 取得したいカラム名
            condition(Dict[str, Any]): 条件

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        assert type(table) is str, table
        assert type(condition) is dict
        assert table != ""

        sql: List[str] = ["SELECT"] + [", ".join(columns)] + ["FROM", table]
        bindee: Optional[List[Any]] = None

        if condition:
            bindee = []
            sql.append("WHERE")
            for cond_k, cond_v in condition.items():
                sql.append("{}=?".format(cond_k))
                bindee.append(cond_v)
                sql.append("AND")
            sql.pop()  # 一番最後のANDを削除

        return self.__execute(" ".join(sql), bindee)

    def search(self, table: str, columns: List[str] = ["*"], condition: Dict[str, Any] = {}) -> list:
        """ データベースからデータを検索する基礎関数

        Args:
            table(str): テーブル名
            columns(List[str]): 取得したいカラム名
            condition(Dict[str, Any]): 検索条件

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        assert type(table) is str, table
        assert type(condition) is dict
        assert table != ""

        sql: List[str] = ["SELECT"] + [", ".join(columns)] + ["FROM", table]
        bindee: Optional[List[Any]] = None

        if condition:
            bindee = []
            sql.append("WHERE")
            for cond_k, cond_v in condition.items():
                sql.append("{} like ?".format(cond_k))
                bindee.append(cond_v)
                sql.append("AND")
            sql.pop()  # 一番最後のANDを削除

        return self.__execute(" ".join(sql), bindee)

    def insert(self, table: str, candidate: Dict[str, Any]) -> Optional[int]:
        """ データベースにデータを挿入する基礎関数

        Args:
            table(str): テーブル名
            candidate(Dict[str, Any]): カラム名とデータのペア

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合
        """
        assert type(table) is str
        assert table != ""
        assert type(candidate) is dict
        assert len(candidate) > 0

        sql = ["INSERT", "INTO"]
        # sql = "INSERT INTO " + table + "("
        cols = []
        vals = []
        for cand_k, cand_v in candidate.items():
            cols.append(cand_k)
            vals.append(cand_v)

        sql.append("{}({})".format(table, ", ".join(cols)))
        sql.append("VALUES({})".format(", ".join("?" * len(vals))))
        return self.__execute(" ".join(sql), vals, request_last_id=True)[0]

    def update(self, table: str, candidate: Dict[str, Any], condition: Dict[str, Any] = {}) -> list:
        """ データベースを更新する基礎関数

        Args:
            table(str): テーブル名
            candidate(Dict[str, Any]): カラム名とデータのペア
            condition(Dict[str, Any]): 条件

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        assert type(table) is str
        assert table != ""
        assert type(candidate) is dict
        assert len(candidate) > 0
        assert type(condition) is dict

        sql = ["UPDATE", table, "SET"]

        cols = []
        vals = []
        for cand_k, cand_v in candidate.items():
            cols.append(cand_k + "=?")
            vals.append(cand_v)
        sql.append(", ".join(cols))

        if condition:
            sql.append("WHERE")
            for cond_k, cond_v in condition.items():
                sql.append("`{}`=?".format(cond_k))
                vals.append(cond_v)
                sql.append("AND")
            sql.pop()  # 一番最後のANDを削除

        return self.__execute(" ".join(sql), vals)

    def insertOrReplace(self, table: str, candidate: Dict[str, Any]) -> list:
        """ データベースへ挿入・更新する基礎関数

        データが存在する場合は更新し、存在しない場合は挿入する。
        カラムにPrimary Key、もしくはUniqueが設定されている場合のみ有効。

        Args:
            table(str): テーブル名
            candidate(Dict[str, Any]): カラム名とデータのペア

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        assert type(table) is str
        assert table != ""
        assert type(candidate) is dict
        assert len(candidate) > 0

        sql = ["INSERT", "OR", "REPLACE", "INTO"]
        cols = []
        vals = []
        for cand_k, cand_v in candidate.items():
            cols.append("'{}'".format(cand_k))
            vals.append(cand_v)

        sql.append("{}({})".format(table, ", ".join(cols)))
        sql.append("VALUES({})".format(", ".join("?" * len(vals))))
        return self.__execute(" ".join(sql), vals, request_last_id=True)

    def delete(self, table: str, condition: Dict[str, Any] = {}):
        """ データベースからデータを削除する基礎関数

        Args:
            table(str): テーブル名
            condition(Dict[str, Any]): 条件

        Exceptions:
            sqlite3.Error: データベースオペレーションでエラーがあった場合

        Returns:
            list: 取得結果が格納されたリスト
        """
        sql = ["DELETE", "FROM", table]
        bindee: Optional[list] = None

        if condition:
            bindee = []
            sql.append("WHERE")
            for cond_k, cond_v in condition.items():
                sql.append("`{}`=?".format(cond_k))
                bindee.append(cond_v)
                sql.append("AND")
            sql.pop()  # 一番最後のANDを削除

        return self.__execute(" ".join(sql), bindee)

    def getLastInsertedId(self) -> int:
        """ 直前に操作したレコードのIDを取得
        """
        return self.__cursor.lastrowid

    def closeCursor(self):
        if self.__cursor is not None:
            self.__cursor.close()
            self.__cursor = None
