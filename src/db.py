import json
import sys
import logging
import mysql.connector as mysql


logger = logging.getLogger(__name__)

try:
    with open("./c.json") as credentials:
        c = json.load(credentials)
        db_config = {
            "user": c.get("mysqluser"),
            "password": c.get("mysqlpw"),
            "host": c.get("mysqlhost"),
        }
except Exception as e:
    logger.critical(f"Failed to load database credentials: {e}")
    sys.exit(1)


try:
    MMO_POOL = mysql.pooling.MySQLConnectionPool(pool_name="rl_pool", pool_size=32, database="rl", **db_config)
    USER_POOL = mysql.pooling.MySQLConnectionPool(pool_name="user_pool", pool_size=32, database="jok.im", **db_config)
except mysql.Error as e:
    logger.critical(f"Failed to initialize connection pools: {e}")
    sys.exit(1)


def get_db_connection(database="rl"):
    try:
        if database == "rl":
            return MMO_POOL.get_connection()
        elif database == "jok.im":
            return USER_POOL.get_connection()
        else:
            raise ValueError(f"Unknown database pool requested: {database}")

    except mysql.PoolError as e:
        logger.error(f"Connection pool exhausted or error encountered: {e}")
        raise e
    except mysql.Error as e:
        logger.critical(f"Database error when fetching connection from pool: {e}")
        sys.exit(1)
