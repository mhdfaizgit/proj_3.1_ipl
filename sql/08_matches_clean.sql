DROP TABLE IF EXISTS matches_clean;
CREATE TABLE matches_clean AS
SELECT m.match_id,
       m.venue_clean,
       c.city_clean,
       s.season_year,
       m.team1,
       m.team2,
       m.result,
       m.match_winner,
       m.player_of_match,
       m.toss_winner,
       m.toss_decision
FROM   v_matches_venue m
JOIN   v_city_clean c ON c.match_id = m.match_id
JOIN   v_season     s ON s.match_id = m.match_id;

