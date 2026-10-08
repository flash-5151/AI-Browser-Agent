import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_task = Column(Text, nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    final_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    executions = relationship("Execution", back_populates="task", cascade="all, delete-orphan")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    status = Column(String(32), default="running", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="executions")
    steps = relationship("ExecutionStep", back_populates="execution", cascade="all, delete-orphan", order_by="ExecutionStep.step_number")


class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    action_input = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    screenshot_b64 = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    execution = relationship("Execution", back_populates="steps")
