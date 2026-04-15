from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    column,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


# Table: groups;
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(50), unique=True, nullable=False)
    create_at = Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"id: {self.id}, group_name: {self.group_name}"

    def __str__(self):
        return f"id: {self.id}, group_name: {self.group_name}"


# Table: students;
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(125), nullable=False)
    last_name = Column(String(125), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column("cell_phone", String(20), nullable=False)
    address = Column(String(100), nullable=False)
    create_at = Column(DateTime, default=datetime.now())
    group_id = Column(
        Integer,
        ForeignKey("groups.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )  #
    group = relationship("Group", backref="students")

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name

    def __repr__(self):
        return f"id: {self.id}, student_name: {self.full_name}"

    def __str__(self):
        return f"id: {self.id}, student_name: {self.full_name}"


# Table: teachers;
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(125), nullable=False)
    last_name = Column(String(125), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column("cell_phone", String(20), nullable=False)
    address = Column(String(100), nullable=False)
    create_at = Column(DateTime, default=datetime.now())

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name

    def __repr__(self):
        return f"id: {self.id}, teacher_name: {self.full_name}"

    def __str__(self):
        return f"id: {self.id}, teacher_name: {self.full_name}"


# Table: subjects;
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_name = Column(String(255), unique=True, nullable=False)
    create_at = Column(DateTime, default=datetime.now())
    teacher_id = Column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    teacher = relationship("Teacher", backref="subjects")

    def __repr__(self):
        return f"id: {self.id}, subject: {self.subject_name}"

    def __str__(self):
        return f"id: {self.id}, subject: {self.subject_name}"


# Table: grades;
class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade = Column(Integer, nullable=False)
    # grade = Column(Integer, CheckConstraint("grade BETWEEN 1 AND 100"), nullable=False)
    grade_date = Column(Date, nullable=False)
    create_at = Column(DateTime, default=datetime.now())
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    student = relationship("Student", backref="grades")
    subject = relationship("Subject", backref="grades")

    __table_args__ = (
        CheckConstraint(column("grade").between(1, 100), name="chk_grade_range"),
        # CheckConstraint("grade >= 1 AND grade <= 100", name="chk_grade_range"),
    )

    def __repr__(self):
        return f"id: {self.id}, grade: {self.grade}, date: {self.grade_date}"

    def __str__(self):
        return f"id: {self.id}, grade: {self.grade}, date: {self.grade_date}"
