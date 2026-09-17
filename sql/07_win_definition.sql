
/*win definition: a match is counted as a win when result ="win"
reason: the result column is designed to identify whether a match was a win and this excludes matches that did not finish */

SELECT * FROM matches WHERE result = 'win';