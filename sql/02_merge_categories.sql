DROP VIEW IF EXISTS V_deliveries_typed;
CREATE VIEW V_deliveries_typed AS
SELECT *, CASE WHEN bowler_type_clean = 'Right arm Fast Medium'
                THEN 'Right arm Fast Medium'
                ELSE bowler_type_clean
           END AS bowler_style
FROM v_deliveries_clean;

DROP VIEW IF EXISTS V_team_clean;
CREATE VIEW V_team_clean AS
SELECT *,
       CASE WHEN team_name = 'Rising Pune Supergiant'
            THEN 'Rising Pune Supergiants'
            ELSE team_name
       END AS team_name_clean
FROM teams;