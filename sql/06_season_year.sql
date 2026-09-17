DROP VIEW IF EXISTS v_season;
CREATE VIEW v_season AS
SELECT match_id,
        season,
        CAST(SUBSTR(season, 1, 4)
            AS INTEGER) AS season_year
FROM matches;