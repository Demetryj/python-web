-- Find a list of students in a specific group

SELECT s.id, s.student_name
FROM students AS s
JOIN groups AS gp ON gp.id = s.group_id
WHERE gp.group_name = %s; 
