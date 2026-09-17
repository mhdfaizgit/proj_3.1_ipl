--deliveries.bowler_type
--player.field_pos
--matches.player_of_match
--contains fix 1,2,3


DROP VIEW IF EXISTS v_deliveries_clean;
CREATE VIEW v_deliveries_clean AS
SELECT *,
       NULLIF(TRIM(bowler_type), '') AS bowler_type_clean
FROM deliveries;   
DROP VIEW IF EXISTS v_players_clean;
CREATE VIEW v_players_clean AS
SELECT *,
        NULLIF(TRIM(field_pos), '') AS field_pos_clean
FROM players;
DROP VIEW IF EXISTS v_matches_clean;
CREATE VIEW v_matches_clean AS
SELECT *,
        NULLIF(TRIM(player_of_match), '') AS pom_clean
FROM matches;