import sqlite3

"""
Reads the provided .csv data from the resources folder and creates
or overwrites 'test.db' in the resources folder.
"""

name = "newest.csv"
conn = sqlite3.connect('../resources/test.db')
c = conn.cursor()

# Drop tables
try:
    c.execute("DROP TABLE games")
    c.execute("DROP TABLE scores")
except sqlite3.Error as e:
    print(e)

# Create them anew
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
    conn.commit()
except sqlite3.Error as e:
    print(e)

# Add data from .csv
with open(f'../resources/{name}') as stats:
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
