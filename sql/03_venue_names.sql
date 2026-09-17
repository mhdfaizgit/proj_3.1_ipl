--one venue 

DROP VIEW IF EXISTS v_matches_venue;
CREATE VIEW v_matches_venue AS
SELECT *,
        REPLACE(
            TRIM(
                SUBSTR(venue, 1,
                    CASE WHEN INSTR(venue,',') > 0
                    THEN INSTR(venue, ',') - 1
                    ELSE LENGTH(venue)
                END)),
            'M Chinnaswamy', 'M chinnaswamy') AS venue_clean
FROM matches;
