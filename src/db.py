import json
import sys
import logging
import mysql.connector as mysql


logger = logging.getLogger(__name__)
CREDENTIALS = dict()  # TODO: Use env


def get_db_connection(database="rl"):
    if not CREDENTIALS:
        try:
            with open("./c.json") as credentials:
                c = json.load(credentials)
                CREDENTIALS["user"] = c.get("mysqluser")
                CREDENTIALS["password"] = c.get("mysqlpw")
                CREDENTIALS["host"] = c.get("mysqlhost")
        except FileNotFoundError as _:
            logger.critical("c.json not found in project root. Aborting...")
            sys.exit(1)
        except KeyError as _:
            logger.critical("One or more required database credentials are missing from c.json")
            sys.exit(1)

    try:
        connection = mysql.connect(
            **CREDENTIALS,
            database=database,
            pool_name=database,
            pool_size=32
        )
    except mysql.DatabaseError as e:
        logger.critical(f"Database error: {e}")
        logger.critical(f"Unable to connect database with user {CREDENTIALS["user"]} at {CREDENTIALS["host"]}:3306")
        sys.exit(1)

    return connection
