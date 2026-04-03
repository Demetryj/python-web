--Find the 5 students with the highest average scores in all subjects.

SELECT s.student_name as name, AVG(g.grade) as average_grade
FROM students as s 
JOIN grades as g ON g.student_id = s.id
GROUP BY student_name
ORDER BY average_grade desc
LIMIT 5;