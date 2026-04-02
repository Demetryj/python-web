DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS groups;

-- Table: groups;
CREATE TABLE groups (
	id SERIAL PRIMARY KEY,
	group_name VARCHAR(50) UNIQUE NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: students;
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    group_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id)
    	ON UPDATE CASCADE
    	ON DELETE SET null,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--Table: teachers;
CREATE TABLE teachers (
	id SERIAL PRIMARY KEY,
	teacher_name VARCHAR(255) NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 

--Table: subjects;
CREATE TABLE subjects(
	id SERIAL PRIMARY KEY,
	subject_name VARCHAR(255) UNIQUE NOT NULL,
	teacher_id INTEGER,
	FOREIGN KEY (teacher_id) REFERENCES teachers(id)
		ON UPDATE CASCADE 
		ON DELETE SET null,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: grades;
CREATE TABLE grades(
	id SERIAL PRIMARY KEY,
	grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 100),
	grade_date DATE NOT NULL,
	student_id INTEGER NOT NULL REFERENCES students(id),
	subject_id INTEGER NOT NULL REFERENCES subjects(id),	
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP	
);
