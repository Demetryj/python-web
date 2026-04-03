-- Find out what courses a particular instructor teaches

SELECT t.teacher_name, sb.subject_name
FROM teachers AS t
JOIN subjects AS sb on sb.teacher_id = t.id
WHERE t.teacher_name = %s;
