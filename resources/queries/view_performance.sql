CREATE VIEW performance AS
SELECT * FROM (
SELECT gameID, playerID, AVG(score) OVER (PARTITION BY playerID ORDER BY GameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS score,
AVG(goals) OVER (PARTITION BY playerID ORDER BY GameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS goals,
AVG(assists) OVER (PARTITION BY playerID ORDER BY GameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS assists,
AVG(saves) OVER (PARTITION BY playerID ORDER BY GameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS saves,
AVG(shots) OVER (PARTITION BY playerID ORDER BY GameID ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS shots
FROM scores ORDER BY gameID) WHERE gameID >= 20
