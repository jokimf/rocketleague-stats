import json

import mysql.connector as mysql


class DatabaseConnection:
    connections: dict[mysql.MySQLConnection] = dict()

    @staticmethod
    def get(table: str = "rl") -> mysql.MySQLConnection:

        # Check if connection to table exists
        existing_connection: mysql.MySQLConnection = DatabaseConnection.connections.get(table)
        if existing_connection is not None and not existing_connection.is_connected():
            existing_connection.reconnect()
        else:
            DatabaseConnection._connect_to_db(table)
        return DatabaseConnection.connections.get(table)

    @staticmethod
    def _connect_to_db(table: str) -> None:
        with open("./c.json") as credentials:
            c = json.load(credentials)
            user = c.get("mysqluser")
            password = c.get("mysqlpw")
            host = c.get("mysqlhost")

        new_connection = mysql.connect(
            user=user,
            password=password,
            host=host,
            database=table,
        )
        DatabaseConnection.connections[table] = new_connection
