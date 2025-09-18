import json

import mysql.connector as mysql


class Database:
    credentials = dict()

    @staticmethod
    def get_connection(database="rl"):
        if not Database.credentials:
            with open("./c.json") as credentials:
                c = json.load(credentials)
                Database.credentials["user"] = c.get("mysqluser")
                Database.credentials["password"] = c.get("mysqlpw")
                Database.credentials["host"] = c.get("mysqlhost")

        connection = mysql.connect(
            **Database.credentials,
            database=database,
            pool_name=database,
            pool_size=32
        )
        # TODO connection may fail?

        return connection