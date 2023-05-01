import sqlite3


def connect_to_database():
    database_path = 'resources/test.db'
    conn = sqlite3.connect(database_path, check_same_thread=False)  # TODO: get rid of same thread check
    return conn
