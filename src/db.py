import json
import sys
import logging
import mysql.connector as mysql


logger = logging.getLogger(__name__)
CREDENTIALS = dict()  # TODO: Use env


def get_db_connection(database="rl"):
    if not CREDENTIALS:
        with open("./c.json") as credentials:
            c = json.load(credentials)
            CREDENTIALS["user"] = c.get("mysqluser")
            CREDENTIALS["password"] = c.get("mysqlpw")
            CREDENTIALS["host"] = c.get("mysqlhost")

    try:
        connection = mysql.connect(
            **CREDENTIALS,
            database=database,
            pool_name=database,
            pool_size=32
        )
    except mysql.DatabaseError as e:
        logger.critical(f"Unable to connect database with user {CREDENTIALS["user"]} at {CREDENTIALS["host"]}:3306")
        sys.exit(1)

    return connection
