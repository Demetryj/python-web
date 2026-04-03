-- The average grade that a particular teacher gives a particular student

SELECT s.student_name, t.teacher_name, ROUND(AVG(g.grade), 2)
FROM students AS s
JOIN grades as g ON g.student_id = s.id
join subjects as sb ON sb.id = g.subject_id  
JOIN teachers AS  t ON t.id = sb.teacher_id 
WHERE s.student_name = %s 
	AND t.TEACHER_NAME = %s
GROUP BY s.student_name, t.teacher_name;
