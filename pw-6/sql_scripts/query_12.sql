-- Student grades in a specific group for a specific subject in the last lesson

SELECT 
	s.student_name, 
	g.grade,
	sb.subject_name,
	g.grade_date AS last_lesson
FROM students AS s
JOIN grades AS g ON g.student_id = s.id
JOIN subjects AS sb ON sb.id = g.subject_id
JOIN groups AS gp ON gp.id = s.group_id
WHERE gp.group_name = 'tu-88'
 	AND sb.subject_name = 'tell reality wide'
 	AND g.grade_date = (
		SELECT MAX(g2.grade_date)
		FROM grades AS g2
  		JOIN students AS s2 ON s2.id = g2.student_id
  		JOIN subjects AS sb2 ON sb2.id = g2.subject_id
  		JOIN groups AS gp2 ON gp2.id = s2.group_id
  		WHERE gp2.group_name = 'tu-88'
			AND sb2.subject_name = 'tell reality wide');
    
