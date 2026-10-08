import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.task import Task, Execution, ExecutionStep
from app.browser.playwright_manager import PlaywrightManager
from app.llm.gemini_service import GeminiService
from app.api.ws import ws_manager

logger = logging.getLogger(__name__)

# Registries for active task sessions and cancellations
active_task_cancellations: Dict[str, bool] = {}
active_orchestrators: Dict[str, "AgentOrchestrator"] = {}

def get_active_orchestrator(task_id: str) -> Optional["AgentOrchestrator"]:
    return active_orchestrators.get(task_id)

def validate_finish_result(user_task: str, result_text: str, page_info: Dict[str, Any]) -> tuple:
    if not result_text or len(result_text.strip()) < 10:
        return False, "Result is empty or too short."
    
    res_lower = result_text.lower()
    task_lower = user_task.lower()
    page_text_lower = page_info.get("text_content", "").lower()
    page_url = page_info.get("url", "").lower()
    
    # 1. Anti-hallucination check: reject unrelated tutorial results unless requested
    if "fastapi" in res_lower and "fastapi" not in task_lower:
        return False, "Result contains unrelated FastAPI content."

    # 2. Reject homepage links / search engine footer links
    homepage_indicators = ["about duckduckgo", "duckduckgo app", "privacy policy", "search settings", "about google", "terms of service", "spreadduckduckgo"]
    if any(ind in res_lower for ind in homepage_indicators) and not any(kw in res_lower for kw in ["car", "cars", "india", "top"]):
        return False, "Result consists of search engine homepage links instead of actual search query results."
    
    # 3. Cannot finish while anti-bot challenge page is active
    if "/sorry" in page_url or page_info.get("is_challenge"):
        return False, "Cannot finish task while anti-bot verification challenge is active."
        
    # 4. Check for task keyword presence or page content alignment
    task_words = [w for w in task_lower.replace("search", "").replace("top", "").replace("the", "").replace("find", "").split() if len(w) > 2]
    if task_words:
        matches = [w for w in task_words if w in res_lower or w in page_text_lower]
        if not matches:
            return False, f"Result does not contain key terms ({task_words}) relevant to the task."
            
    return True, "Valid"

class AgentOrchestrator:
    def __init__(self, task_id: Optional[str] = None, websocket_broadcaster: Optional[Any] = None):
        self.task_id = task_id
        self.websocket_broadcaster = websocket_broadcaster
        self.gemini = GeminiService()
        self.browser_manager = PlaywrightManager(headless=settings.HEADLESS)
        self.resume_event = asyncio.Event()

    def trigger_resume(self):
        logger.info(f"Triggering resume for task {self.task_id}")
        self.resume_event.set()

    async def broadcast_event(self, data: dict):
        if self.task_id:
            await ws_manager.broadcast(self.task_id, data)
            if self.websocket_broadcaster:
                try:
                    await self.websocket_broadcaster(self.task_id, data)
                except Exception as e:
                    logger.error(f"Error calling custom websocket_broadcaster: {e}")

    async def run_task(self, task_id: str, db: Optional[Session] = None):
        self.task_id = task_id
        await self.run(db=db)

    async def run(self, db: Optional[Session] = None):
        if not self.task_id:
            logger.error("Cannot run orchestrator without a valid task_id.")
            return

        db_created = False
        if db is None:
            db = SessionLocal()
            db_created = True

        task = db.query(Task).filter(Task.id == self.task_id).first()
        if not task:
            logger.error(f"Task {self.task_id} not found.")
            if db_created:
                db.close()
            return

        # Register active orchestrator
        active_orchestrators[self.task_id] = self
        active_task_cancellations[self.task_id] = False
        self.resume_event.clear()

        # Create or update execution record
        execution = Execution(task_id=self.task_id, status="running", started_at=datetime.utcnow())
        db.add(execution)
        task.status = "running"
        db.commit()
        db.refresh(execution)

        history = []
        final_result_text = ""

        try:
            logger.info(f"Starting browser agent for task: {task.user_task}")
            await self.browser_manager.start()

            await self.broadcast_event({
                "type": "status_update",
                "status": "running",
                "message": "Browser started. Initiating agent execution loop...",
                "step_number": 0
            })

            step_number = 1
            max_steps = settings.MAX_AGENT_STEPS

            while step_number <= max_steps:
                # Check for user cancellation
                if active_task_cancellations.get(self.task_id, False):
                    logger.info(f"Task {self.task_id} cancelled by user.")
                    task.status = "cancelled"
                    execution.status = "cancelled"
                    execution.completed_at = datetime.utcnow()
                    db.commit()

                    await self.broadcast_event({
                        "type": "task_cancelled",
                        "status": "cancelled",
                        "message": "Task was cancelled by user."
                    })
                    break

                # 1. Observe current page
                page_info = await self.browser_manager.get_page_info()
                screenshot_b64 = await self.browser_manager.get_screenshot_b64()

                # Anti-bot / CAPTCHA challenge pause check
                if page_info.get("is_challenge") or "/sorry" in page_info.get("url", "").lower():
                    logger.warning(f"Anti-bot challenge detected for task {self.task_id}: {page_info.get('challenge_reason')}")
                    
                    task.status = "HUMAN_VERIFICATION_REQUIRED"
                    execution.status = "HUMAN_VERIFICATION_REQUIRED"
                    db.commit()

                    status_message = "STATUS: HUMAN_VERIFICATION_REQUIRED"
                    print(f"[WS BROADCAST] ⚠️ {status_message}")

                    await self.broadcast_event({
                        "type": "human_verification_required",
                        "status": "HUMAN_VERIFICATION_REQUIRED",
                        "message": status_message,
                        "url": page_info["url"],
                        "title": page_info["title"],
                        "screenshot_b64": screenshot_b64
                    })

                    self.resume_event.clear()
                    # Sleep State: Do not proceed with any steps until the URL no longer contains /sorry/ and page is clear
                    while not self.resume_event.is_set():
                        if active_task_cancellations.get(self.task_id, False):
                            break
                        await asyncio.sleep(1)
                        cur_info = await self.browser_manager.get_page_info()
                        if not cur_info.get("is_challenge") and "/sorry" not in cur_info.get("url", "").lower():
                            logger.info("Auto-detected verification completion! Target page is visible.")
                            self.resume_event.set()
                            break

                    if active_task_cancellations.get(self.task_id, False):
                        continue

                    logger.info(f"Resuming task {self.task_id} post-verification")
                    task.status = "running"
                    execution.status = "running"
                    db.commit()

                    await self.broadcast_event({
                        "type": "verification_completed",
                        "status": "running",
                        "message": "Human verification completed. Resuming browser agent execution..."
                    })

                    self.resume_event.clear()
                    # Re-observe page after verification completed
                    page_info = await self.browser_manager.get_page_info()
                    screenshot_b64 = await self.browser_manager.get_screenshot_b64()

                # Broadcast current page state to live UI
                await self.broadcast_event({
                    "type": "page_observation",
                    "step_number": step_number,
                    "url": page_info["url"],
                    "title": page_info["title"],
                    "screenshot_b64": screenshot_b64,
                    "status": "AI is deciding next action..."
                })

                # 2. Gemini decides next action
                decision = await self.gemini.decide_next_action(
                    user_task=task.user_task,
                    history=history,
                    current_page_info=page_info
                )

                thought = decision.get("thought", "")
                action_name = decision.get("action", "wait")
                args = decision.get("args", {})

                # Prevent duplicate fill actions
                if action_name == "fill" and history:
                    last_step = history[-1]
                    if last_step.get("action") == "fill" and last_step.get("args", {}).get("text") == args.get("text"):
                        logger.info("Preventing duplicate fill action. Pressing Enter instead.")
                        action_name = "press"
                        args = {"key": "Enter"}
                        thought = "Search query already filled. Pressing Enter to submit search."

                # Validate finish action
                if action_name == "finish":
                    candidate_result = args.get("result", "")
                    is_valid, reason = validate_finish_result(task.user_task, candidate_result, page_info)
                    if not is_valid:
                        logger.warning(f"Rejected finish action: {reason}")
                        action_name = "wait"
                        args = {"seconds": 2}
                        thought = f"Finish rejected ({reason}). Re-observing current page for valid search results."

                # Broadcast AI decision
                await self.broadcast_event({
                    "type": "action_decided",
                    "step_number": step_number,
                    "thought": thought,
                    "action": action_name,
                    "args": args,
                    "url": page_info["url"],
                    "title": page_info["title"],
                    "screenshot_b64": screenshot_b64
                })

                # 3. Execute action
                action_result_msg = ""
                if action_name == "navigate":
                    url_to_nav = args.get("url", "https://example.com")
                    action_result_msg = await self.browser_manager.navigate(url_to_nav)
                elif action_name == "click":
                    selector = args.get("selector", "")
                    action_result_msg = await self.browser_manager.click(selector)
                elif action_name == "fill":
                    selector = args.get("selector", "")
                    text_val = args.get("text", "")
                    action_result_msg = await self.browser_manager.fill(selector, text_val)
                elif action_name == "press":
                    key_val = args.get("key", "Enter")
                    action_result_msg = await self.browser_manager.press(key_val)
                    # Observe fresh page state immediately after press (e.g. Enter)
                    await asyncio.sleep(1.5)
                elif action_name == "scroll":
                    direction = args.get("direction", "down")
                    action_result_msg = await self.browser_manager.scroll(direction)
                elif action_name == "wait":
                    secs = float(args.get("seconds", 2))
                    action_result_msg = await self.browser_manager.wait(secs)
                elif action_name == "extract_text":
                    action_result_msg = await self.browser_manager.extract_text()
                elif action_name == "go_back":
                    action_result_msg = await self.browser_manager.go_back()
                elif action_name == "finish":
                    final_result_text = args.get("result", "Task completed successfully.")
                    action_result_msg = f"Task completed: {final_result_text}"
                else:
                    action_result_msg = f"Unknown action: {action_name}"

                # Post-action screenshot & update
                post_page_info = await self.browser_manager.get_page_info()
                post_screenshot_b64 = await self.browser_manager.get_screenshot_b64()

                # Record step in database
                step_record = ExecutionStep(
                    execution_id=execution.id,
                    step_number=step_number,
                    action=action_name,
                    action_input=json.dumps(args),
                    result=action_result_msg[:1000],
                    url=post_page_info["url"],
                    screenshot_b64=post_screenshot_b64
                )
                db.add(step_record)
                db.commit()

                # Update history for Gemini context
                history.append({
                    "step": step_number,
                    "action": action_name,
                    "args": args,
                    "thought": thought,
                    "result": action_result_msg,
                    "url": post_page_info["url"]
                })

                # Broadcast completed step update
                await self.broadcast_event({
                    "type": "step_completed",
                    "step_number": step_number,
                    "action": action_name,
                    "args": args,
                    "thought": thought,
                    "result": action_result_msg,
                    "url": post_page_info["url"],
                    "title": post_page_info["title"],
                    "screenshot_b64": post_screenshot_b64
                })

                if action_name == "finish":
                    task.status = "completed"
                    task.final_result = final_result_text
                    execution.status = "completed"
                    execution.completed_at = datetime.utcnow()
                    db.commit()

                    await self.broadcast_event({
                        "type": "task_completed",
                        "status": "completed",
                        "final_result": final_result_text,
                        "screenshot_b64": post_screenshot_b64
                    })
                    break

                step_number += 1

            if step_number > max_steps and task.status == "running":
                task.status = "completed"
                task.final_result = final_result_text or "Reached maximum step limit."
                execution.status = "completed"
                execution.completed_at = datetime.utcnow()
                db.commit()

                await self.broadcast_event({
                    "type": "task_completed",
                    "status": "completed",
                    "final_result": task.final_result
                })

        except Exception as e:
            logger.error(f"Error running agent orchestrator: {e}", exc_info=True)
            task.status = "failed"
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            db.commit()

            await self.broadcast_event({
                "type": "task_failed",
                "status": "failed",
                "error": str(e)
            })
        finally:
            await self.browser_manager.stop()
            active_task_cancellations.pop(self.task_id, None)
            active_orchestrators.pop(self.task_id, None)
            if db_created:
                db.close()
