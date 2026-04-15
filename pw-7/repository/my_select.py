from sqlalchemy import func, desc, Float, select, and_
from sqlalchemy.orm import Session, joinedload

from conf.models import Group, Student, Teacher, Subject, Grade


def select_1(session: Session):
    """Find the 5 students with the highest average scores in all subjects."""

    students = (
        session.query(
            Student.full_name,
            func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade"),
        )
        .join(Grade, Grade.student_id == Student.id)
        .group_by(Student.full_name)
        .order_by(desc("average_grade"))
        .limit(5)
        .all()
    )
    return students


def select_2(session: Session, discipline: str = ""):
    """Find the student with the highest average score in a particular subject."""

    # It is possible not to use the full_name hybrid_property from the Student(Base) model
    # and instead construct the full name directly in the query`
    stmt = (
        select(
            func.concat(Student.first_name, " ", Student.last_name).label(
                "student_name"
            ),
            Subject.subject_name,
            func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade"),
        )
        .join(Student, Student.id == Grade.student_id)
        .join(Subject, Subject.id == Grade.subject_id)
        .where(Subject.subject_name == discipline)
        .group_by(Student.first_name, Student.last_name, Subject.subject_name)
        .order_by(desc("average_grade"))
        .limit(1)
    )

    result = session.execute(stmt)
    return result.mappings().all()


def select_3(session: Session, discipline: str = ""):
    """Find the average score in groups in a specific subject."""

    result = (
        session.query(
            Group.group_name,
            Subject.subject_name,
            func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade"),
        )
        .join(Student, Student.id == Grade.student_id)
        .join(Group, Group.id == Student.group_id)
        .join(Subject, Subject.id == Grade.subject_id)
        .filter(Subject.subject_name == discipline)
        .group_by(Group.group_name, Subject.subject_name)
        .all()
    )
    return result


def select_4(session: Session):
    """Find the average score on the stream (across the entire grade table)."""

    stmt = select(
        func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade")
    )
    result = session.execute(stmt)
    return result.mappings().first()


def select_5(session: Session, lector: str = ""):
    """Find out what courses a particular instructor teaches"""

    result = None

    response = (
        session.query(Teacher.full_name, Subject.subject_name)
        .join(Subject, Subject.teacher_id == Teacher.id)
        .filter(Teacher.full_name == lector)
        .all()
    )

    if response:
        for r in response:
            labels = ["teacher", "subject"]
            result = dict(zip(labels, (r.full_name, r.subject_name)))

    return result


def select_6(session: Session, group: str = ""):
    "Find a list of students in a specific group"

    result = None

    response = (
        session.query(Student.id, Student.full_name, Group.group_name)
        .join(Student.group)
        .filter(Group.group_name == group)
        .all()
    )

    if response:
        labels = ["id", "student", "group"]

        result = [
            dict(zip(labels, (r.id, r.full_name, r.group_name))) for r in response
        ]

    return result


def select_7(session: Session, group: str = "", discipline: str = ""):
    """Find the grades of students in a particular group in a specific subject."""

    stmt = (
        select(
            Student.id,
            func.concat(Student.first_name, " ", Student.last_name).label("full_name"),
            Group.group_name,
            Subject.subject_name,
            Grade.grade,
            Grade.grade_date,
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Group, Group.id == Student.group_id)
        .join(Subject, Subject.id == Grade.subject_id)
        .where(and_(Group.group_name == group, Subject.subject_name == discipline))
    )

    result = session.execute(stmt)
    return result.mappings().all()


def select_8(session: Session, lector: str = ""):
    """Find the average score that a certain teacher gives in their subjects."""

    result = (
        session.query(
            Teacher.id,
            Teacher.full_name,
            func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade"),
        )
        .join(Subject, Subject.teacher_id == Teacher.id)
        .join(Grade, Grade.subject_id == Subject.id)
        .filter(Teacher.full_name == lector)
        .group_by(Teacher.id, Teacher.full_name)
        .all()
    )

    return result


def select_9(session: Session, student: str = ""):
    """Find a list of courses a student is taking."""

    result = None

    response = (
        session.query(Subject.id, Subject.subject_name, Student.full_name)
        .join(Grade, Grade.subject_id == Subject.id)
        .join(Student, Student.id == Grade.student_id)
        .filter(Student.full_name == student)
        .order_by(Subject.id)
        .distinct()
        .all()
    )

    if response:
        labels = ["id", "subject", "student"]
        result = [
            dict(zip(labels, (s.id, s.subject_name, s.full_name))) for s in response
        ]
    return result


def select_10(session: Session, student: str = "", lector: str = ""):
    """A list of courses taught by a specific teacher to a specific student."""

    response = (
        session.query(Subject.id, Subject.subject_name)
        .join(Grade, Grade.subject_id == Subject.id)
        .join(Student, Student.id == Grade.student_id)
        .join(Teacher, Teacher.id == Subject.teacher_id)
        .filter(and_(Student.full_name == student, Teacher.full_name == lector))
        .distinct()
        .all()
    )

    return response


def select_11(session: Session, student: str = "", lector: str = ""):
    """The average grade that a particular teacher gives a particular student."""

    stmt = (
        select(
            Student.full_name.label("student"),
            Teacher.full_name.label("teacher"),
            func.round(func.avg(Grade.grade), 2).cast(Float).label("average_grade"),
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Subject, Subject.id == Grade.subject_id)
        .join(Teacher, Teacher.id == Subject.teacher_id)
        .where(and_(Teacher.full_name == lector, Student.full_name == student))
        .group_by(Student.full_name, Teacher.full_name)
    )

    result = session.execute(stmt)
    return result.mappings().all()


def select_12(session: Session, group: str = "", discipline: str = ""):
    """Student grades in a specific group for a specific subject in the last lesson."""

    max_date_subq = (
        select(func.max(Grade.grade_date))
        .join(Student, Student.id == Grade.student_id)
        .join(Subject, Subject.id == Grade.subject_id)
        .join(Group, Group.id == Student.group_id)
        .where(and_(Group.group_name == group, Subject.subject_name == discipline))
        .scalar_subquery()
    )

    stmt = (
        select(
            Student.full_name.label("student_name"),
            Grade.grade,
            Subject.subject_name,
            Grade.grade_date.label("last_lesson"),
        )
        .join(Grade, Grade.student_id == Student.id)
        .join(Subject, Subject.id == Grade.subject_id)
        .join(Group, Group.id == Student.group_id)
        .where(
            and_(
                Group.group_name == group,
                Subject.subject_name == discipline,
                Grade.grade_date == max_date_subq,
            )
        )
    )

    result = session.execute(stmt)
    return result.mappings().all()
