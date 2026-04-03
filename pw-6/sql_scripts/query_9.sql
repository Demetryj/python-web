-- Find a list of courses a student is taking

SELECT DISTINCT sb.id, sb.subject_name, s.student_name
FROM subjects AS sb
JOIN grades AS g ON g.subject_id  = sb.id
JOIN students AS s ON s.id = g.student_id
WHERE s.student_name = %s
ORDER by sb.id;
