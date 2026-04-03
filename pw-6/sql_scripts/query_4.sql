-- Find the average score on the stream (across the entire grade table).

SELECT AVG(g.grade) as average_grade
FROM grades as g;