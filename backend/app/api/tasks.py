import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.task import Task, Execution, ExecutionStep
from app.schemas.task import TaskCreate, TaskSchema, TaskDetailSchema, ExecutionSchema
from app.agent.orchestrator import AgentOrchestrator, active_task_cancellations, get_active_orchestrator
from app.api.ws import ws_manager

router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "AI Browser Agent Backend"}

@router.post("/tasks", response_model=TaskSchema)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    task = Task(user_task=task_in.user_task, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/tasks", response_model=List[TaskSchema])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return tasks

@router.get("/tasks/{task_id}", response_model=TaskDetailSchema)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).options(joinedload(Task.executions).joinedload(Execution.steps)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/tasks/{task_id}/run", response_model=TaskSchema)
def run_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == "running":
        raise HTTPException(status_code=400, detail="Task is already running")

    task.status = "running"
    db.commit()
    db.refresh(task)

    orchestrator = AgentOrchestrator(task_id)
    background_tasks.add_task(orchestrator.run)

    return task

@router.get("/tasks/{task_id}/execution", response_model=ExecutionSchema)
def get_task_execution(task_id: str, db: Session = Depends(get_db)):
    execution = db.query(Execution).options(joinedload(Execution.steps)).filter(Execution.task_id == task_id).order_by(Execution.started_at.desc()).first()
    if not execution:
        raise HTTPException(status_code=404, detail="No execution found for this task")
    return execution

@router.post("/tasks/{task_id}/resume")
def resume_task(task_id: str, db: Session = Depends(get_db)):
    orchestrator = get_active_orchestrator(task_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="No active orchestrator session found for this task")
    
    orchestrator.trigger_resume()
    return {"message": f"Resume signal sent for task {task_id}"}

@router.post("/tasks/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    active_task_cancellations[task_id] = True
    task.status = "cancelled"
    db.commit()

    return {"message": f"Cancellation requested for task {task_id}"}

@router.websocket("/tasks/{task_id}/ws")
async def task_websocket(websocket: WebSocket, task_id: str):
    await ws_manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(task_id, websocket)
