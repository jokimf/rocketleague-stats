import database as db

name = 'newest.csv'
conn = db.connect_to_database()
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
            rank TEXT NOT NULL CHECK(rank IN ('',' ','GC','D1','D2','D3','C1','C2','C3','GC1','GC2','GC3','SSL')),
            score INTEGER NOT NULL CHECK(score>=0),
            goals INTEGER NOT NULL CHECK(goals>=0),
            assists INTEGER NOT NULL CHECK(assists>=0),
            saves INTEGER NOT NULL CHECK(saves>=0),
            shots INTEGER NOT NULL CHECK(shots>=0),
            PRIMARY KEY(gameID,playerID)
        );       
        """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            gameID INTEGER PRIMARY KEY,
            date TEXT NOT NULL CHECK(date IS strftime('%Y-%m-%d', date)),
            goals INTEGER NOT NULL CHECK(goals>=0),
            against INTEGER NOT NULL CHECK(against>=0)
        ); 
        """)
    conn.commit()
except sqlite3.Error as e:
    print(e)

# Add data from .csv
with open(f'resources/{name}') as stats:
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
