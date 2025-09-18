from connect import Database

name = 'newest.csv'
conn = Database.get_connection()
c = conn.cursor()

# Drop tables
c.execute("DROP TABLE IF EXISTS scores")
c.execute("DROP TABLE IF EXISTS games")

# Create them anew
c.execute("""
        CREATE TABLE `games` (
        `gameID` int NOT NULL,
        `date` text NOT NULL,
        `goals` int NOT NULL,
        `against` int NOT NULL,
        PRIMARY KEY (`gameID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """)
c.execute("""
        CREATE TABLE `scores` (
        `gameID` int NOT NULL,
        `playerID` int NOT NULL,
        `rank` text NOT NULL,
        `score` int NOT NULL,
        `goals` int NOT NULL,
        `assists` int NOT NULL,
        `saves` int NOT NULL,
        `shots` int NOT NULL,
        PRIMARY KEY (`gameID`,`playerID`),
        KEY `scores_players_FK` (`playerID`),
        CONSTRAINT `scores_games_FK` FOREIGN KEY (`gameID`) REFERENCES `games` (`gameID`),
        CONSTRAINT `scores_players_FK` FOREIGN KEY (`playerID`) REFERENCES `players` (`playerID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
    """)
conn.commit()

# Add data from .csv
with open(f'./{name}') as stats:
    for line in stats:
        data = line.split(',')
        games_data = [data[0], data.pop(1), data.pop(1), data.pop(1)]
        c.execute("INSERT INTO games VALUES(%s,%s,%s,%s)", games_data)
        knus = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
        puad = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
        sticker = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
        c.execute("INSERT INTO scores VALUES(%s,0,%s,%s,%s,%s,%s,%s)", knus)
        c.execute("INSERT INTO scores VALUES(%s,1,%s,%s,%s,%s,%s,%s)", puad)
        c.execute("INSERT INTO scores VALUES(%s,2,%s,%s,%s,%s,%s,%s)", sticker)
c.close()
conn.commit()
