-- Find the average score in groups in a specific subject

SELECT 
    gr.group_name,
    sb.subject_name,
    AVG(g.grade) AS average_grade
FROM grades AS g
JOIN students AS s ON s.id = g.student_id
JOIN groups AS gr ON gr.id = s.group_id
JOIN subjects AS sb ON sb.id = g.subject_id
WHERE sb.subject_name = %s
GROUP BY gr.group_name, sb.subject_name;