import sqlite3
import time
import os

def connect_to_database():
    database_path = 'resources/test.db'
    #try:
    conn = sqlite3.connect(database_path, check_same_thread=False)  # TODO: get rid of same thread check
    #except sqlite3.OperationalError:
       # pass
    return conn
