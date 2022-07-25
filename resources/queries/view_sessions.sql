CREATE VIEW sessions as
SELECT row_number() OVER (ORDER BY date) as SessionID, date, SUM(g.goals) as "Goals", SUM(g.against) as "Against", 
SUM(k.score) as "KnusScore", SUM(k.goals) as "KnusGoals", SUM(k.assists) as "KnusAssists",SUM(k.saves) as "KnusSaves", SUM(k.shots) as "KnusShots",
SUM(p.score) as "PuadScore", SUM(p.goals) as "PuadGoals", SUM(p.assists) as "PuadAssists",SUM(p.saves) as "PuadSaves", SUM(p.shots) as "PuadShots",
SUM(s.score) as "StickerScore", SUM(s.goals) as "StickerGoals", SUM(s.assists) as "StickerAssists",SUM(s.saves) as "StickerSaves", SUM(s.shots) as "StickerShots"
FROM games g LEFT JOIN knus k ON g.gameID = k.gameID LEFT JOIN puad p ON g.gameID = p.gameID LEFT JOIN sticker s ON g.gameID = s.gameID GROUP BY date