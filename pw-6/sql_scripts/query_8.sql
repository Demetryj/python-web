-- Find the average score that a certain teacher gives in their subjects

SELECT 
    t.id,
    t.teacher_name,
    ROUND(AVG(g.grade), 2) AS average_grade
FROM teachers AS t
JOIN subjects AS sb ON sb.teacher_id = t.id
JOIN grades AS g ON g.subject_id = sb.id
WHERE t.teacher_name = %s
GROUP BY t.id, t.teacher_name;
