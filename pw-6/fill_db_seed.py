from faker import Faker
from psycopg2 import Error

from random import randint

from connection import create_connection

"""
Generate fake data to populate database tables.
1. Generate names for groups, students, teachers, and subjects.
2. Prepare data according to table columns.
   Fields such as id and created_at are not provided manually because they are
   filled automatically by SQL defaults.
3. Insert prepared fake data into the database.
"""

fake = Faker("en_US")

NUMBER_STUDENTS = 50
NUMBER_GROUPS = 3
NUMBER_SUBJECTS = 8
NUMBERS_TEACHERS = 5
NUMBER_GRADES_PER_STUDENT = 20

Row = tuple[str | int, ...]
Rows = list[Row]

sql_to_groups = """
INSERT INTO groups (group_name)
VALUES (%s)
"""

sql_to_students = """
INSERT INTO students (student_name, group_id)
VALUES (%s, %s)
"""

sql_to_teachers = """
INSERT INTO teachers (teacher_name)
VALUES (%s)
"""

sql_to_subjects = """
INSERT INTO subjects (subject_name, teacher_id)
VALUES (%s, %s)
"""

sql_to_grades = """
INSERT INTO grades (grade, grade_date, student_id, subject_id)
VALUES (%s, %s, %s, %s)
"""

sql_truncate_all = """
TRUNCATE TABLE grades, subjects, students, teachers, groups
RESTART IDENTITY CASCADE
"""


def generate_fake_data(
    number_groups: int, number_students: int, number_teachers: int, number_subjects: int
) -> tuple[list[str], ...]:
    """Generate fake groups, students, teachers, and subjects."""
    fake_groups = []
    fake_students = []
    fake_teachers = []
    fake_subjects = []

    # Generate group names.
    for _ in range(number_groups):
        group_name = fake.bothify(text="??-##")
        fake_groups.append(group_name)

    # Generate student names.
    for _ in range(number_students):
        student_name = fake.name()
        fake_students.append(student_name)

    # Generate teacher names.
    for _ in range(number_teachers):
        teacher_name = fake.name()
        fake_teachers.append(teacher_name)

    # Generate subject names.
    for _ in range(number_subjects):
        subject = " ".join(fake.words(nb=3))
        fake_subjects.append(subject)

    return fake_groups, fake_students, fake_teachers, fake_subjects


def prepare_data(
    groups: list[str],
    students: list[str],
    teachers: list[str],
    subjects: list[str],
    number_grade_per_student: int,
) -> tuple[Rows, ...]:
    """Prepare row tuples for bulk inserts into all tables."""

    # Build a list of tuples for groups.
    group_data = [(group,) for group in groups]

    # Build a list of tuples for teachers.
    teacher_data = [(teacher,) for teacher in teachers]

    # Build a list of tuples for students.
    student_data = []

    for student in students:
        group_id = randint(1, len(groups))
        student_data.append((student, group_id))

    # Build a list of tuples for subjects.
    subject_data = []

    for subject in subjects:
        teacher_id = randint(1, len(teachers))
        subject_data.append((subject, teacher_id))

    # Build a list of grade tuples.
    # Each student receives up to number_grade_per_student grades.
    grade_data = []

    for student_id in range(1, len(students) + 1):
        for _ in range(number_grade_per_student):
            subject_id = randint(1, len(subjects))
            grade = randint(1, 100)
            grade_date = fake.date_this_year()
            grade_data.append((grade, grade_date, student_id, subject_id))

    return group_data, student_data, teacher_data, subject_data, grade_data


def insert_data_to_db(
    groups: Rows, students: Rows, teachers: Rows, subjects: Rows, grades: Rows
) -> None:
    """Insert prepared data into the database within one transaction."""

    # Open a database connection.
    with create_connection() as connection:
        cursor = None
        try:
            # Get a cursor object.
            cursor = connection.cursor()
            # Clear previous seed data and reset identity counters.
            cursor.execute(sql_truncate_all)
            # Execute parameterized SQL commands.
            cursor.executemany(sql_to_groups, groups)
            cursor.executemany(sql_to_students, students)
            cursor.executemany(sql_to_teachers, teachers)
            cursor.executemany(sql_to_subjects, subjects)
            cursor.executemany(sql_to_grades, grades)
            # Commit pending transactions to persist inserted rows.
            connection.commit()
        except Error as err:
            # Roll back all changes if any database operation fails.
            connection.rollback()
            print(err)
            raise
        finally:
            if cursor is not None:
                # Close the cursor manually.
                cursor.close()

        # Alternative without manual cursor close:
        # with create_connection() as connection:
        #     try:
        #         with connection.cursor() as cursor:
        #             cursor.executemany(sql_to_groups, groups)
        #             cursor.executemany(sql_to_students, students)
        #             cursor.executemany(sql_to_teachers, teachers)
        #             cursor.executemany(sql_to_subjects, subjects)
        #             cursor.executemany(sql_to_grades, grades)
        #         connection.commit()
        #     except Error as err:
        #         connection.rollback()
        #         print(err)
        #         raise


if __name__ == "__main__":
    fake_data = generate_fake_data(
        number_groups=NUMBER_GROUPS,
        number_students=NUMBER_STUDENTS,
        number_teachers=NUMBERS_TEACHERS,
        number_subjects=NUMBER_SUBJECTS,
    )

    data_for_insert = prepare_data(
        *fake_data, number_grade_per_student=NUMBER_GRADES_PER_STUDENT
    )

    insert_data_to_db(*data_for_insert)
