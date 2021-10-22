from sqlite3 import Error
import sqlite3

conn = None
c = None


def import_data_from_csv():
    with open('C:/Users/Jokim/code-workspace/RocketLeagueSQL/Database/newest.csv') as stats:
        for line in stats:
            data = line.split(',')
            games_data = [data[0], data.pop(1), data.pop(1), data.pop(1)]
            c.execute("INSERT INTO games VALUES(?,?,?,?)", games_data)
            knus = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            puad = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            sticker = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            c.execute("INSERT INTO scores VALUES(?,0,?,?,?,?,?,?)", knus)
            c.execute("INSERT INTO scores VALUES(?,1,?,?,?,?,?,?)", puad)
            c.execute("INSERT INTO scores VALUES(?,2,?,?,?,?,?,?)", sticker)

    c.close()
    conn.commit()


def create_tables():
    try:
        c.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            gameID INTEGER,
            playerID INTEGER,
            rank TEXT NOT NULL,
            score INTEGER NOT NULL,
            goals INTEGER NOT NULL,
            assists INTEGER NOT NULL,
            saves INTEGER NOT NULL,
            shots INTEGER NOT NULL,
            PRIMARY KEY(gameID,playerID)
        );       
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            gameID INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            goals INTEGER NOT NULL,
            against INTEGER NOT NULL
        ); 
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            playerID INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        """)

        c.execute("INSERT INTO players VALUES(0,'Knus')")
        c.execute("INSERT INTO players VALUES(1,'Puad')")
        c.execute("INSERT INTO players VALUES(2,'Sticker')")
        conn.commit()
    except Error as e:
        print(e)


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn


def drop_tables():
    try:
        c.execute("DROP TABLE players")
        c.execute("DROP TABLE games")
        c.execute("DROP TABLE scores")
    except Error as e:
        print(e)


if __name__ == '__main__':
    conn = create_connection('test.db')
    c = conn.cursor()
    drop_tables()
    create_tables()
    import_data_from_csv()
