import asyncio
import base64
import logging
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class PlaywrightManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.firefox.launch(
                headless=self.headless
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(15000)

    async def stop(self):
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error stopping Playwright: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    async def get_screenshot_b64(self) -> str:
        if not self.page:
            return ""
        try:
            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=70)
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return ""

    async def get_page_info(self) -> Dict[str, Any]:
        if not self.page:
            return {
                "url": "about:blank",
                "title": "No page active",
                "interactive_elements": [],
                "text_content": "",
                "is_challenge": False,
                "challenge_reason": ""
            }
        
        try:
            url = self.page.url
            title = await self.page.title()
            
            # Extract interactive elements with selectors
            elements_script = """
            () => {
                const elements = [];
                const nodes = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [role="link"], [onclick]');
                let index = 1;
                nodes.forEach(node => {
                    const rect = node.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(node).visibility !== 'hidden';
                    if (!isVisible) return;
                    
                    let tag = node.tagName.toLowerCase();
                    let text = (node.innerText || node.value || node.getAttribute('placeholder') || node.getAttribute('aria-label') || node.getAttribute('title') || '').trim();
                    text = text.replace(/\\s+/g, ' ').slice(0, 80);
                    
                    let id = node.id ? '#' + node.id : '';
                    let name = node.getAttribute('name') ? `[name="${node.getAttribute('name')}"]` : '';
                    let selector = id ? tag + id : (name ? tag + name : tag);
                    
                    if (text && (tag === 'button' || tag === 'a')) {
                        selector = `text="${text}"`;
                    } else if (id) {
                        selector = id;
                    } else if (node.getAttribute('placeholder')) {
                        selector = `[placeholder="${node.getAttribute('placeholder')}"]`;
                    }
                    
                    elements.push({
                        idx: index++,
                        tag: tag,
                        text: text,
                        selector: selector,
                        href: node.getAttribute('href') || '',
                        type: node.getAttribute('type') || ''
                    });
                });
                return elements.slice(0, 50);
            }
            """
            interactive_elements = await self.page.evaluate(elements_script)
            
            # Extract clean main page text
            text_script = """
            () => {
                const body = document.body;
                if (!body) return "";
                return body.innerText.replace(/\\s+/g, ' ').slice(0, 3000);
            }
            """
            text_content = await self.page.evaluate(text_script)

            # Anti-bot / CAPTCHA challenge detection logic
            lower_url = url.lower()
            lower_text = text_content.lower()
            lower_title = title.lower()

            is_challenge = False
            challenge_reason = ""

            if "/sorry" in lower_url or "google.com/sorry" in lower_url:
                is_challenge = True
                challenge_reason = "Google redirect to /sorry (anti-bot page)"
            elif any(phrase in lower_text or phrase in lower_title for phrase in [
                "unusual traffic",
                "robot verification",
                "i am not a robot",
                "i'm not a robot",
                "verify you are a human",
                "verify you're a human",
                "recaptcha",
                "hcaptcha",
                "pardon the interruption",
                "confirm you are not a robot"
            ]):
                is_challenge = True
                challenge_reason = f"Anti-bot verification detected on page (Title: '{title}')"

            return {
                "url": url,
                "title": title,
                "interactive_elements": interactive_elements,
                "text_content": text_content,
                "is_challenge": is_challenge,
                "challenge_reason": challenge_reason
            }
        except Exception as e:
            logger.error(f"Error extracting page info: {e}")
            return {
                "url": getattr(self.page, "url", "unknown"),
                "title": "Error reading page",
                "interactive_elements": [],
                "text_content": f"Error: {str(e)}",
                "is_challenge": False,
                "challenge_reason": ""
            }

    # Browser Tools Implementation
    async def navigate(self, url: str) -> str:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        await self.page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(1)
        title = await self.page.title()
        return f"Successfully navigated to {url}. Page title: '{title}'"

    async def click(self, selector: str) -> str:
        try:
            # First try directly
            await self.page.click(selector, timeout=5000)
            await asyncio.sleep(1)
            return f"Clicked element matching '{selector}'"
        except Exception:
            # Fallback to text search if selector failed
            try:
                await self.page.get_by_text(selector).first.click(timeout=5000)
                await asyncio.sleep(1)
                return f"Clicked text matching '{selector}'"
            except Exception as e:
                return f"Failed to click '{selector}': {str(e)}"

    async def fill(self, selector: str, text: str) -> str:
        # List of candidate selectors to try for robust fill
        candidate_selectors = [
            selector,
            "#searchbox_input",
            "input[name='q']",
            "textarea[name='q']",
            "input[type='search']",
            "input[type='text']",
            "input[placeholder*='Search' i]",
            "input[aria-label*='Search' i]",
            "[role='searchbox']"
        ]
        
        for sel in candidate_selectors:
            if not sel:
                continue
            try:
                elem = self.page.locator(sel).first
                if await elem.is_visible(timeout=1000):
                    await elem.fill(text, timeout=2000)
                    return f"Filled element '{sel}' with text '{text}'"
            except Exception:
                continue

        # Last attempt via evaluate JS if Playwright locators failed
        try:
            filled = await self.page.evaluate("""
                (text) => {
                    const input = document.querySelector('#searchbox_input, input[name="q"], textarea[name="q"], input[type="text"], input[type="search"]');
                    if (input) {
                        input.value = text;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                    return false;
                }
            """, text)
            if filled:
                return f"Filled search input via JS with text '{text}'"
        except Exception:
            pass

        return f"Failed to fill input using selector '{selector}'. No visible search input found on page."

    async def press(self, key: str) -> str:
        await self.page.keyboard.press(key)
        await asyncio.sleep(1)
        return f"Pressed key '{key}'"

    async def scroll(self, direction: str) -> str:
        if direction.lower() == "down":
            await self.page.evaluate("window.scrollBy(0, 600)")
        elif direction.lower() == "up":
            await self.page.evaluate("window.scrollBy(0, -600)")
        await asyncio.sleep(0.5)
        return f"Scrolled {direction}"

    async def wait(self, seconds: float) -> str:
        secs = min(max(seconds, 0.5), 10.0)
        await asyncio.sleep(secs)
        return f"Waited {secs} seconds"

    async def extract_text(self) -> str:
        page_info = await self.get_page_info()
        return f"Page URL: {page_info['url']}\nTitle: {page_info['title']}\nText:\n{page_info['text_content']}"

    async def go_back(self) -> str:
        await self.page.go_back()
        await asyncio.sleep(1)
        return f"Navigated back to {self.page.url}"
