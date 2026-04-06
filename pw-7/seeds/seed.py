from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session

from random import randint

from conf.models import Group, Student, Teacher, Subject, Grade
from conf.db import get_session

"""Creating fake data and filling out tables"""

fake = Faker("en_US")

NUMBER_STUDENTS = 50
NUMBER_GROUPS = 3
NUMBER_SUBJECTS = 8
NUMBERS_TEACHERS = 5
NUMBER_GRADES_PER_STUDENT = 20


def create_groups() -> list[Group]:
    """Create a list of study groups."""

    return [Group(group_name=fake.bothify(text="??-##")) for _ in range(NUMBER_GROUPS)]


def create_students(groups: list[Group]) -> list[Student]:
    """Create students and assign each one to a random group."""

    student_data = []
    for _ in range(NUMBER_STUDENTS):
        student = Student(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            phone=fake.phone_number()[:20],
            address=fake.address()[:100],
            group_id=fake.random_element(groups).id,
        )
        student_data.append(student)
    return student_data


def create_subjects(teachers: list[Teacher]) -> list[Subject]:
    """Create subjects and assign each one to a random teacher."""

    return [
        Subject(
            subject_name=" ".join(fake.unique.words(nb=3)),
            teacher_id=fake.random_element(teachers).id,
        )
        for _ in range(NUMBER_SUBJECTS)
    ]


def create_teachers() -> list[Teacher]:
    """Create a list of teachers."""

    return [
        Teacher(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email(),
            phone=fake.phone_number()[:20],
            address=fake.address()[:100],
        )
        for _ in range(NUMBERS_TEACHERS)
    ]


def create_grades(students: list[Student], subjects: list[Subject]) -> list[Grade]:
    """Create random grades for each student across random subjects."""

    grades = []

    for student in students:
        for _ in range(NUMBER_GRADES_PER_STUDENT):
            grades.append(
                Grade(
                    grade=randint(1, 100),
                    grade_date=fake.date_this_year(),
                    student_id=student.id,
                    subject_id=fake.random_element(subjects).id,
                )
            )
    return grades


def clear_tables(session: Session) -> None:
    """Remove old data and reset identities before inserting fresh seed data."""

    session.execute(
        text(
            "TRUNCATE TABLE grades, students, subjects, teachers, groups "
            "RESTART IDENTITY CASCADE"
        )
    )


def seed():
    """Fill database tables with fake groups, students, teachers, subjects, and grades."""

    with get_session() as session:
        # Clear all tables first so repeated seed runs do not duplicate data.
        clear_tables(session)
         
        groups = create_groups()
        session.add_all(groups)
        # flush() sends INSERTs to DB without commit, so new rows get
        # generated IDs (e.g., group.id, teacher.id)
        # that we need immediately for foreign keys in the next objects.
        session.flush()

        students = create_students(groups)
        session.add_all(students)
        session.flush()

        teachers = create_teachers()
        session.add_all(teachers)
        session.flush()

        subjects = create_subjects(teachers)
        session.add_all(subjects)
        session.flush()

        grades = create_grades(students=students, subjects=subjects)
        session.add_all(grades)

        # commit() is called automatically when exiting the with block
        # because get_session() is implemented using a context manager


if __name__ == "__main__":
    seed()
