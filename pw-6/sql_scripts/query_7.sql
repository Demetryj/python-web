-- Find the grades of students in a particular group in a specific subject

SELECT 
	s.id,
	s.student_name, 
	sb.subject_name, 
	gp.group_name,
	g.grade
FROM grades AS g
JOIN students AS s ON s.id = g.student_id
JOIN groups as gp ON gp.id =  s.group_id
JOIN subjects AS sb ON sb.id = g.subject_id
WHERE gp.group_name = %s' AND sb.subject_name = %s; 