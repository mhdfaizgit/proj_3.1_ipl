DROP VIEW IF EXISTS v_city_clean;
CREATE VIEW v_city_clean AS
SELECT m.match_id,
        COALESCE(v.city,
                 m.city,
                 'UNKNOWN' ) AS city_clean
FROM v_matches_venue m 
JOIN v_venues_clean v 
        ON v.venue = m.venue;

