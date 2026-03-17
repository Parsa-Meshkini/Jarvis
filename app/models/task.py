import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(str, Enum):
    QUEUED    = "queued"
    PLANNING  = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED    = "failed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_request: Mapped[str]      = mapped_column(Text, nullable=False)
    status:       Mapped[str]      = mapped_column(String(20), default=TaskStatus.QUEUED)
    result:       Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at:   Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at:   Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    steps: Mapped[list["TaskStep"]] = relationship(
        "TaskStep", back_populates="task", order_by="TaskStep.created_at"
    )


class TaskStep(Base):
    __tablename__ = "task_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id:    Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    step_name:  Mapped[str]        = mapped_column(String(100))
    status:     Mapped[str]        = mapped_column(String(20), default="pending")
    output:     Mapped[str|None]   = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped["Task"] = relationship("Task", back_populates="steps")


class UserMemory(Base):
    """
    Stores persistent user preferences and context.
    One row per key — upserted on every save.
    """
    __tablename__ = "user_memory"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[str]        = mapped_column(String(100), nullable=False, index=True)
    key:        Mapped[str]        = mapped_column(String(100), nullable=False)
    value:      Mapped[str]        = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:      Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    name:       Mapped[str]       = mapped_column(String(100), nullable=False)
    password:   Mapped[str]       = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)