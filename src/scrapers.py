# src/scrapers.py
from playwright.async_api import Page
from src.config import JOBS_PER_COMPANY, TIMEOUT_MS, JOB_KEYWORDS
from urllib.parse import urlparse
import asyncio
import random

async def handle_interruptions(page: Page):
    """Closes cookie banners or popups."""
    try:
        selectors = [
            "button[id*='cookie']", "button[class*='cookie']", 
            "button[text*='Accept']", "div[role='dialog'] button:has-text('Accept all')",
            "div[id*='onetrust'] button", # Common cookie banner
        ]
        for sel in selectors:
            if await page.locator(sel).first.is_visible():
                await page.locator(sel).first.click(timeout=1000)
    except:
        pass

async def duckduckgo_search(page: Page, query: str):
    """Generic search function using DuckDuckGo."""
    try:
        await page.goto("https://duckduckgo.com", timeout=TIMEOUT_MS)
        await handle_interruptions(page)

        search_box = page.locator("input[name='q']")
        await search_box.click() 
        await search_box.fill(query)
        await search_box.press("Enter")
        
        await page.wait_for_selector("a[data-testid='result-title-a']", timeout=TIMEOUT_MS)
        
        first_result = page.locator("a[data-testid='result-title-a']").first
        url = await first_result.get_attribute("href")
        
        await asyncio.sleep(random.uniform(1.0, 2.0))
        return url
    except Exception:
        return None

def extract_home_page(url):
    """Extracts root domain (e.g., https://careers.google.com -> https://google.com)"""
    if not url: return "N/A"
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        parts = domain.split('.')
        if len(parts) > 2 and parts[-2] not in ['co', 'com', 'org', 'net']: 
            domain = ".".join(parts[-2:])
        return f"{parsed.scheme}://{domain}"
    except:
        return url

async def get_page_description(page: Page):
    """Extracts the meta description from the current page."""
    try:
        # Javascript to get <meta name="description"> content
        desc = await page.evaluate("""() => {
            const meta = document.querySelector('meta[name="description"]');
            return meta ? meta.content : '';
        }""")
        if desc:
            return desc[:200] + "..." # Limit length
        return "See Website"
    except:
        return "See Website"

# --- SCRAPERS ---

async def scrape_zoho(page: Page):
    jobs = []
    try:
        await page.wait_for_load_state('networkidle', timeout=TIMEOUT_MS)
        links = await page.locator("li a, div.job-title a, h4 a").all()
        for link in links[:JOBS_PER_COMPANY]:
            title = await link.inner_text()
            href = await link.get_attribute("href")
            if title and len(title) > 3 and "\n" not in title:
                jobs.append({"Title": title.strip(), "Url": href})
    except: pass
    return jobs

async def scrape_lever(page: Page):
    jobs = []
    try:
        await page.wait_for_selector(".posting", timeout=TIMEOUT_MS)
        postings = await page.locator(".posting").all()
        for post in postings[:JOBS_PER_COMPANY]:
            title = await post.locator("h5").inner_text()
            href = await post.locator("a.posting-title").get_attribute("href")
            jobs.append({"Title": title, "Url": href})
    except: pass
    return jobs

async def scrape_generic_fallback(page: Page, url: str):
    jobs = []
    try:
        await page.wait_for_selector("body", timeout=TIMEOUT_MS)
        await handle_interruptions(page)
        links = await page.locator("a[href]").all()
        count = 0
        for link in links:
            if count >= JOBS_PER_COMPANY: break
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                if any(k in text.lower() for k in JOB_KEYWORDS) and len(text) < 80:
                    full_link = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                    jobs.append({"Title": text.strip(), "Url": full_link})
                    count += 1
            except: continue
    except: pass
    return jobs

async def determine_and_scrape(page: Page, url: str):
    try:
        await page.goto(url, timeout=TIMEOUT_MS)
        
        # Determine scraper
        jobs = []
        if "zoho" in url:
            jobs = await scrape_zoho(page)
        elif "lever.co" in url:
            jobs = await scrape_lever(page)
        else:
            jobs = await scrape_generic_fallback(page, url)
            
        # Extract description while we are on the page
        desc = await get_page_description(page)
        return jobs, desc
    except Exception:
        return [], "N/A"