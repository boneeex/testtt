from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, text, ForeignKey, JSON
from typing import Annotated, List, Dict
import datetime 
import enum

from src.database import Base


idpk = Annotated[int, mapped_column(primary_key=True)]
reqstr = Annotated[str, mapped_column(nullable=False)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


class UserOrm(Base): 
    __tablename__ = 'users'

    id: Mapped[idpk]
    name: Mapped[str] = mapped_column(default="Имя не указано")
    test_passed: Mapped[int] = mapped_column(default=0)
    session_fk: Mapped[int] = mapped_column(ForeignKey("sessions.id"))

    session: Mapped["SessionOrm"] = relationship(back_populates="users")


class TeachersOrm(Base):
    __tablename__ = "teachers"

    id: Mapped[idpk]
    name: Mapped[reqstr]
    email: Mapped[reqstr] = mapped_column(unique=True)
    password_hash: Mapped[reqstr]
    #many
    tasks: Mapped[List["TaskOrm"]] = relationship(back_populates="teacher")
    comments: Mapped[List["CommentsOrm"]] = relationship(back_populates="teacher")
    session: Mapped[List["SessionOrm"]] = relationship(back_populates="teacher")


class TaskOrm(Base):
    __tablename__ = "tasks"

    id: Mapped[idpk]
    title: Mapped[reqstr] = mapped_column(String(50), unique=True)
    task_text: Mapped[reqstr] = mapped_column(String(500))
    time_created: Mapped[created_at]
    teacher_fk: Mapped[int] = mapped_column(ForeignKey("teachers.id"))

    teacher: Mapped["TeachersOrm"] = relationship(back_populates="tasks")

    tests: Mapped[List["TestsOrm"]] = relationship(back_populates="task")
    comments: Mapped[List["CommentsOrm"]] = relationship(back_populates="task")
    session: Mapped[List["SessionOrm"]] = relationship(back_populates="task")


class IsStarted(enum.Enum):
    started = "started"
    pending = "pending"
    finished = "finished"


class SessionOrm(Base):
    __tablename__ = "sessions"

    id: Mapped[idpk]
    deadline_time: Mapped[datetime.datetime]
    status: Mapped[IsStarted] = mapped_column(default=IsStarted.pending)
    unique_code: Mapped[str] = mapped_column(unique=True)
    task_fk: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    teacher_fk: Mapped[int] = mapped_column(ForeignKey("teachers.id"))

    teacher: Mapped["TeachersOrm"] = relationship(back_populates="session")
    task: Mapped["TaskOrm"] = relationship(back_populates="session")
    users: Mapped[List["UserOrm"]] = relationship(back_populates="session")


class TestsOrm(Base):
    __tablename__ = "tests"

    id: Mapped[idpk]
    #{"str": "str"}
    input: Mapped[Dict] = mapped_column(JSON)
    output: Mapped[Dict] = mapped_column(JSON)
    task_fk: Mapped[int] = mapped_column(ForeignKey("tasks.id"))

    task: Mapped["TaskOrm"] = relationship(back_populates="tests")

class CommentsOrm(Base):
    __tablename__ = "comments"

    id: Mapped[idpk]
    text: Mapped[reqstr] = mapped_column(String(300))
    time_created: Mapped[created_at]
    task_fk: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    teacher_fk: Mapped[int] = mapped_column(ForeignKey("teachers.id"))

    task: Mapped["TaskOrm"] = relationship(back_populates="comments")
    teacher: Mapped["TeachersOrm"] = relationship(back_populates="comments")
