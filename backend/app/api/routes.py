import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.task import Task
from app.api.websocket_manager import manager
from app.agent.orchestrator import AgentOrchestrator, active_task_cancellations

logger = logging.getLogger("browser_agent.api")
router = APIRouter(prefix="/tasks", tags=["tasks"])

async def websocket_broadcaster(task_id: str, data: dict):
    await manager.broadcast_to_task(task_id, data)

@router.post("", response_model=dict)
def create_task(payload: dict, db: Session = Depends(get_db)):
    user_task = payload.get("user_task")
    if not user_task:
        raise HTTPException(status_code=400, detail="user_task is required")
    
    task = Task(user_task=user_task, status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "user_task": task.user_task, "status": task.status, "created_at": task.created_at.isoformat()}

@router.get("", response_model=List[dict])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "user_task": t.user_task,
            "status": t.status,
            "final_result": t.final_result,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]

@router.get("/{task_id}", response_model=dict)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    executions = []
    for exec_item in task.executions:
        steps = [
            {
                "id": s.id,
                "step_number": s.step_number,
                "action": s.action,
                "action_input": s.action_input,
                "result": s.result,
                "url": s.url,
                "screenshot_b64": s.screenshot_b64,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in exec_item.steps
        ]
        executions.append({
            "id": exec_item.id,
            "status": exec_item.status,
            "started_at": exec_item.started_at.isoformat() if exec_item.started_at else None,
            "completed_at": exec_item.completed_at.isoformat() if exec_item.completed_at else None,
            "steps": steps
        })

    return {
        "id": task.id,
        "user_task": task.user_task,
        "status": task.status,
        "final_result": task.final_result,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "executions": executions
    }

@router.post("/{task_id}/run", response_model=dict)
async def run_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in ["running", "waiting_for_user_verification"]:
        raise HTTPException(status_code=400, detail="Task is already running or waiting for verification")

    task.status = "running"
    db.commit()

    orchestrator = AgentOrchestrator(task_id)
    background_tasks.add_task(orchestrator.run)
    return {"status": "started", "task_id": task_id}

@router.post("/{task_id}/cancel", response_model=dict)
def cancel_task(task_id: str):
    active_task_cancellations[task_id] = True
    return {"status": "cancel_requested", "task_id": task_id}

@router.websocket("/{task_id}/ws")
async def task_websocket(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WS text from client for task {task_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
