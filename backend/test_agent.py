import asyncio
import json
import logging
from app.database.session import SessionLocal, Base, engine
from app.models.task import Task
from app.agent.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.INFO)

async def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    test_task = Task(    user_task = "Search for the current weather in Hyderabad", status="pending")
    db.add(test_task)
    db.commit()
    db.refresh(test_task)

    print(f"Created Cars Task ID: {test_task.id}")
    orchestrator = None

    async def sample_broadcaster(task_id: str, data: dict):
        nonlocal orchestrator
        event_type = data.get('type')
        if event_type == 'human_verification_required':
            print(f"[WS BROADCAST] ⚠️ HUMAN VERIFICATION REQUIRED: {data.get('message')}")
            # Simulate user completing verification in the active Playwright browser session
            async def delayed_resume():
                await asyncio.sleep(2)
                print("[TEST SIMULATION] User completing Google verification in active Playwright session...")
                if orchestrator and orchestrator.browser_manager and orchestrator.browser_manager.page:
                    # Navigate active page to actual search results page (simulating solved CAPTCHA redirect)
                    await orchestrator.browser_manager.page.goto("https://www.caranddriver.com/rankings/best-sports-cars")
                    await asyncio.sleep(1)
                print("[TEST SIMULATION] User clicked RESUME button!")
                if orchestrator:
                    orchestrator.trigger_resume()
            asyncio.create_task(delayed_resume())
        elif event_type == 'verification_completed':
            print(f"[WS BROADCAST] ✅ VERIFICATION COMPLETED: {data.get('message')}")
        elif event_type == 'action_started':
            print(f"[WS BROADCAST] Action Started: {data.get('action')} | Thought: {data.get('thought')}")
        elif event_type == 'step_completed':
            print(f"[WS BROADCAST] Step {data.get('step')} Completed: {data.get('action')}")
        elif event_type == 'task_completed':
            print(f"[WS BROADCAST] 🎉 TASK COMPLETED!")

    orchestrator = AgentOrchestrator(websocket_broadcaster=sample_broadcaster)
    await orchestrator.run_task(test_task.id, db)

    db.refresh(test_task)
    print(f"\n--- TEST TASK COMPLETED ---")
    print(f"Status: {test_task.status}")
    print(f"Final Result:\n{test_task.final_result}")

if __name__ == "__main__":
    asyncio.run(main())
