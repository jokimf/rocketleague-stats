import mysql.connector as mysql
import json
from dataclasses import dataclass

@dataclass
class Config:
    players: list[dict]
    google_sheets: bool


def init():
    with open("./c.json") as credentials:
        c = json.load(credentials)
        user = c.get("mysqluser")
        password = c.get("mysqlpw")
        host = c.get("mysqlhost")

    with open("./init.json") as initfile:
        file = json.load(initfile)
        players = file.get("players")
        google_sheets = file.get("google_sheets")

    new_connection = mysql.connect(
        user=user,
        password=password,
        host=host,
        buffered=True
    )

    with new_connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS rl;")

    new_connection = mysql.connect(
        user=user,
        password=password,
        host=host,
        buffered=True,
        database="rl"
    )        

    with new_connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `games` (
            `gameID` int NOT NULL,
            `sessionID` int NOT NULL,
            `date` text NOT NULL,
            `goals` int NOT NULL,
            `against` int NOT NULL,
            PRIMARY KEY (`gameID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `meta` (
            `last_reload` int NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""                    
        CREATE TABLE IF NOT EXISTS `players` (
            `playerID` int NOT NULL AUTO_INCREMENT,
            `name` text NOT NULL,
            `color` varchar(100) NOT NULL,
            `active` tinyint(1) NOT NULL DEFAULT '1',
            PRIMARY KEY (`playerID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""                    
        CREATE TABLE IF NOT EXISTS `ranks` (
            `rankID` int NOT NULL AUTO_INCREMENT,
            `rank_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
            `abbr` varchar(3) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
            PRIMARY KEY (`rankID`)
        ) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""CREATE TABLE IF NOT EXISTS `seasons` (
            `seasonID` int NOT NULL,
            `start_date` text NOT NULL,
            `end_date` text NOT NULL,
            `season_name` text NOT NULL,
            PRIMARY KEY (`seasonID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""                    
        CREATE TABLE IF NOT EXISTS `scores` (
            `gameID` int NOT NULL,
            `playerID` int NOT NULL,
            `rankID` int NOT NULL,
            `score` int NOT NULL,
            `goals` int NOT NULL,
            `assists` int NOT NULL,
            `saves` int NOT NULL,
            `shots` int NOT NULL,
            PRIMARY KEY (`gameID`,`playerID`),
            KEY `scores_players_FK` (`playerID`),
            CONSTRAINT `scores_games_FK` FOREIGN KEY (`gameID`) REFERENCES `games` (`gameID`),
            CONSTRAINT `scores_players_FK` FOREIGN KEY (`playerID`) REFERENCES `players` (`playerID`),
            CONSTRAINT `scores_ranks_FK` FOREIGN KEY (`rankID`) REFERENCES `ranks` (`rankID`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)
                       
        cursor.execute("""
        CREATE OR REPLACE
        ALGORITHM = UNDEFINED VIEW `rl`.`performance` AS
        SELECT
            `rf`.`gameID` AS `gameID`,
            `rf`.`playerID` AS `playerID`,
            `rf`.`score` AS `score`,
            `rf`.`goals` AS `goals`,
            `rf`.`assists` AS `assists`,
            `rf`.`saves` AS `saves`,
            `rf`.`shots` AS `shots`
        FROM (
            SELECT
                `rl`.`scores`.`gameID` AS `gameID`,
                `rl`.`scores`.`playerID` AS `playerID`,
                AVG(`rl`.`scores`.`score`) OVER (PARTITION BY `rl`.`scores`.`playerID` ORDER BY `rl`.`scores`.`gameID` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS `score`,
                AVG(`rl`.`scores`.`goals`) OVER (PARTITION BY `rl`.`scores`.`playerID` ORDER BY `rl`.`scores`.`gameID` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS `goals`,
                AVG(`rl`.`scores`.`assists`) OVER (PARTITION BY `rl`.`scores`.`playerID` ORDER BY `rl`.`scores`.`gameID` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS `assists`,
                AVG(`rl`.`scores`.`saves`) OVER (PARTITION BY `rl`.`scores`.`playerID` ORDER BY `rl`.`scores`.`gameID` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS `saves`,
                AVG(`rl`.`scores`.`shots`) OVER (PARTITION BY `rl`.`scores`.`playerID` ORDER BY `rl`.`scores`.`gameID` ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS `shots`
            FROM `rl`.`scores`
            ORDER BY `rl`.`scores`.`gameID`) `rf`
        WHERE `rf`.`gameID` >= 20;
        """)
                       
        cursor.execute("""
        CREATE OR REPLACE
        ALGORITHM = UNDEFINED VIEW `rl`.`mvplvp` AS 
        WITH `max_scores` AS (
            SELECT
                `rl`.`scores`.`gameID` AS `gameID`,
                max(`rl`.`scores`.`score`) AS `max_score`
            FROM `rl`.`scores`
            GROUP BY `rl`.`scores`.`gameID`),
        `min_scores` AS (
            SELECT
                `rl`.`scores`.`gameID` AS `gameID`,
                min(`rl`.`scores`.`score`) AS `min_score`
            FROM `rl`.`scores`
            GROUP BY `rl`.`scores`.`gameID`),
        `mvp` AS (
            SELECT
                `s`.`gameID` AS `gameID`,
                `s`.`playerID` AS `MVP`
            FROM (`rl`.`scores` `s`
            JOIN `max_scores` `ms` ON
                (((`s`.`gameID` = `ms`.`gameID`)
                    and (`s`.`score` = `ms`.`max_score`))))),
        `lvp` AS (
            SELECT
                `s`.`gameID` AS `gameID`,
                `s`.`playerID` AS `LVP`
            FROM (`rl`.`scores` `s`
            JOIN `min_scores` `ms` ON
                (((`s`.`gameID` = `ms`.`gameID`)
                    and (`s`.`score` = `ms`.`min_score`)))))
        SELECT
            `mvp`.`gameID` AS `gameID`,
            `mvp`.`MVP` AS `MVP`,
            `lvp`.`LVP` AS `LVP`
        FROM (`mvp`
        JOIN `lvp` on ((`mvp`.`gameID` = `lvp`.`gameID`)));
        """)
                       
        cursor.execute("""  
        CREATE OR REPLACE
        ALGORITHM = UNDEFINED VIEW `rl`.`sessions` AS 
        SELECT
            ROW_NUMBER() OVER (ORDER BY `g`.`date` ) AS `sessionID`,
            `g`.`date` AS `date`,
            SUM((CASE WHEN (`g`.`goals` > `g`.`against`) THEN 1 ELSE 0 END)) AS `wins`,
            SUM((CASE WHEN (`g`.`goals` < `g`.`against`) then 1 ELSE 0 END)) AS `losses`,
            SUM(`g`.`goals`) AS `Goals`,
            SUM(`g`.`against`) AS `Against`
        FROM `rl`.`games` `g`
        GROUP BY `g`.`date`
        """)

        cursor.execute("""
        INSERT IGNORE INTO `seasons` VALUES 
            (1,'2015-08-09','2016-02-11','I'),
            (2,'2016-02-12','2016-06-20','II'),
            (3,'2016-06-21','2017-03-22','III'),
            (4,'2017-03-23','2017-07-05','IV'),
            (5,'2017-07-06','2017-09-28','V'),
            (6,'2017-09-29','2018-02-07','VI'),
            (7,'2018-02-08','2018-05-29','VII'),
            (8,'2018-05-30','2018-09-24','VIII'),
            (9,'2018-09-25','2019-02-18','IX'),
            (10,'2019-02-19','2019-05-13','X'),
            (11,'2019-05-14','2019-08-27','XI'),
            (12,'2019-08-28','2019-12-04','XII'),
            (13,'2019-12-05','2020-03-25','XIII'),
            (14,'2020-03-26','2020-09-23','XIV'),
            (15,'2020-09-24','2020-12-09','1'),
            (16,'2020-12-10','2021-03-31','2'),
            (17,'2021-04-01','2021-08-11','3'),
            (18,'2021-08-12','2021-11-17','4'),
            (19,'2021-11-18','2022-03-09','5'),
            (20,'2022-03-10','2022-06-14','6'),
            (21,'2022-06-15','2022-09-06','7'),
            (22,'2022-09-07','2022-12-06','8'),
            (23,'2022-12-07','2023-03-07','9'),
            (24,'2023-03-08','2023-06-07','10'),
            (25,'2023-06-08','2023-09-05','11'),
            (26,'2023-09-06','2023-12-06','12'),
            (27,'2023-12-07','2024-03-06','13'),
            (28,'2024-03-07','2024-06-05','14'),
            (29,'2024-06-06','2024-09-04','15'),
            (30,'2024-09-05','2024-12-04','16'),
            (31,'2024-12-05','2025-03-14','17'),
            (32,'2025-03-15','2029-12-31','18');
        """)
                       
        cursor.execute("""          
        INSERT IGNORE INTO `ranks` VALUES 
            (1 ,'Unranked','u'),
            (2 ,'Bronze 1','b1'),
            (3 ,'Bronze 2','b2'),
            (4 ,'Bronze 3','b3'),
            (5 ,'Silver 1','s1'),
            (6 ,'Silver 2','s2'),
            (7 ,'Silver 3','s3'),
            (8 ,'Gold 1','g1'),
            (9 ,'Gold 2','g2'),
            (10,'Gold 3','g3'),
            (11,'Platinum 1','p1'),
            (12,'Platinum 2','p2'),
            (13,'Platinum 3','p3'),
            (14,'Diamond 1','d1'),
            (15,'Diamond 2','d2'),
            (16,'Diamond 3','d3'),
            (17,'Champion 1','c1'),
            (18,'Champion 2','c2'),
            (19,'Champion 3','c3'),
            (20,'Grand Champion 1','gc1'),
            (21,'Grand Champion 2','gc2'),
            (22,'Grand Champion 3','gc3'),
            (23,'Supersonic Legend','ssl');
        """)

        cursor.executemany("INSERT INTO players VALUES (NULL, %s, %s, 1)", [(player["name"], player["color"]) for player in players])

        # testing data

        cursor.execute("""          
        INSERT IGNORE INTO `games` VALUES 
            (1, 1, '2025-04-15', 3, 0),
        """)

        cursor.execute("""          
        INSERT IGNORE INTO `scores` VALUES 
            (1, 1, 10, 500, 1, 2, 3, 5),
            (1, 2, 9, 560, 2, 0, 4, 5),
            (1, 3, 10, 200, 0, 1, 0, 2);
        """)
    new_connection.commit()

if __name__ == "__main__":
    init()