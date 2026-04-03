-- Find the student with the highest average score in a particular subject.

SELECT s.student_name, sb.subject_name, AVG(g.grade) AS average_grade
FROM grades AS g
JOIN students AS s ON s.id = g.student_id
JOIN subjects AS sb ON sb.id = g.subject_id
WHERE sb.subject_name = %s
GROUP BY s.student_name, sb.subject_name
ORDER BY average_grade DESC
LIMIT 1;
