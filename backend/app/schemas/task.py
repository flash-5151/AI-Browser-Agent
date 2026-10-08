from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class TaskCreate(BaseModel):
    user_task: str

class ExecutionStepSchema(BaseModel):
    id: str
    execution_id: str
    step_number: int
    action: str
    action_input: Optional[str] = None
    result: Optional[str] = None
    url: Optional[str] = None
    screenshot_b64: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExecutionSchema(BaseModel):
    id: str
    task_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[ExecutionStepSchema] = []

    class Config:
        from_attributes = True

class TaskSchema(BaseModel):
    id: str
    user_task: str
    status: str
    final_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskDetailSchema(TaskSchema):
    executions: List[ExecutionSchema] = []

    class Config:
        from_attributes = True
