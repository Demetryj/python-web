-- A list of courses taught by a specific teacher to a specific student

SELECT DISTINCT sb.id AS subject_id, sb.subject_name
FROM subjects AS sb
JOIN grades as g ON g.subject_id = sb.id
JOIN students AS s ON s.id = g.student_id
JOIN teachers AS t on t.id = sb.teacher_id 
WHERE s.student_name = %s 
	AND t.TEACHER_NAME = %s;
