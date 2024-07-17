import json

import mysql.connector as mysql

connections = dict()
def get_cursor(table: str):
    global connections
    if not connections.get(table):
        with open("./c.json") as credentials:
            c = json.load(credentials)
            user = c.get("mysqluser")
            password = c.get("mysqlpw")
            host = c.get("mysqlhost")

        connection = mysql.connect(
            user=user, 
            password=password,
            host=host,
            database=table
        )
        connections[table] = connection
    return connections[table], connections[table].cursor()

class BackendConnection:
    def __init__(self, database_name = "rl") -> None:
        connection, cursor = get_cursor(database_name)
        self.connection = connection
        self.c = cursor