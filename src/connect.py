import json

import mysql.connector as mysql

connections = dict()
def get_cursor(table: str = "ungameable"):
    global connections
    existing_connection = connections.get(table)
    if not existing_connection:
        with open("./c.json") as credentials:
            c = json.load(credentials)
            user = c.get("mysqluser")
            password = c.get("mysqlpw")
            host = c.get("mysqlhost")

        new_connection = mysql.connect(
            user=user, 
            password=password,
            host=host,
            database=table
        )
        connections[table] = new_connection
    else:
        if not existing_connection.is_connected():
            existing_connection.reconnect()
            if not existing_connection.is_connected():
                raise ConnectionError("MySQL tried to reconnect, but couldn't.")
    return connections[table], connections[table].cursor()

class BackendConnection:
    def __init__(self) -> None:
        connection, cursor = get_cursor()
        self.connection = connection
        self.c = cursor