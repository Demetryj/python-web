-- Find the average score on the stream (across the entire grade table).

SELECT ROUND(AVG(g.grade), 2) as average_grade
FROM grades as g;