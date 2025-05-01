
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from site_configs import SITE_CONFIGS
import asyncio
# from datetime import datetime
import time

class PlaywrightScraper:
    def __init__(self, domain):
        self.domain = domain
        self.product_patterns = SITE_CONFIGS.get(domain, {}).get("product_url_patterns", [])
        self.infinite_scroll = SITE_CONFIGS.get(domain, {}).get("infinite_scroll", False)

        self.domain_netloc = urlparse(domain).netloc
        self.visited_urls = set()
        self.all_product_links = set()

        self.pagination_selector_or_text = SITE_CONFIGS.get(domain, {}).get("pagination_selector_or_text")
        self.max_pagination_pages = SITE_CONFIGS.get(domain, {}).get("max_pagination_pages", 1)
        self.pop_up_text = SITE_CONFIGS.get(domain, {}).get("pop_up_text", "")
        self.infinite_loader_text = SITE_CONFIGS.get(domain, {}).get("infinite_loader_text", [])

    def is_internal_link(self, url):
        return urlparse(url).netloc == "" or urlparse(url).netloc == self.domain_netloc

    def is_product_url(self, url):
        for pattern in self.product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    async def scroll_to_bottom(self, page, loading_selector_or_text=None):

        seen_heights = set()
        scroll_count = 0

        while True and scroll_count < 100:
            # print(f"[SCROLL] Scroll attempt: {scroll_count + 1}")
            scroll_count += 1
            try:
                # STEP 1: Try to find the loading element by selector or inner text
                # loading_element = None

                # if loading_selector_or_text:
                    # First try direct selector
                    # loading_element = await page.query_selector(loading_selector_or_text)

                    # If not found, try text-based matching
                    # if not loading_element:
                        # print(f"[SEARCH] Trying to find element with text: {loading_selector_or_text}")
                        # loading_element = await page.query_selector(f"text={loading_selector_or_text}")
                for loading in  loading_selector_or_text:   
                    loading_element = await page.query_selector(f"text={loading}")

                    # if not loading_element:
                        # print(f"[SEARCH] Trying to find element with text: {'Loading'}")
                        # loading_element = await page.query_selector(f"text={'Loading'}")

                if not loading_element:
                    break

                # STEP 2: Scroll the loading element into view
                await loading_element.scroll_into_view_if_needed()

                # STEP 3: Wait for it to disappear
                # await page.wait_for_selector(f"text={loading_selector_or_text}", state='detached', timeout=10000)
                # print("[LOADING] Element disappeared. New content may have loaded.")

                max_wait_time = 5000  
                interval = 500        
                waited = 0
                prev_height = await page.evaluate('document.body.scrollHeight')
                while waited < max_wait_time:
                    await page.wait_for_timeout(interval)
                    new_height = await page.evaluate('document.body.scrollHeight')
                    if new_height > prev_height:
                        break
                    waited += interval
                else:
                    print("[TIMEOUT] No new content detected.")

                # STEP 4: Track page height to know when we're done
                current_height = await page.evaluate('document.body.scrollHeight')
                if current_height in seen_heights:
                    # print("[END] No new content detected after scroll.")
                    break
                seen_heights.add(current_height)

            except Exception as e:
                # print(f"[ERROR] Scrolling or waiting failed: {e}")
                break

    async def handle_pagination(self, page, base_url, soup, extract_links_fn):
        # print(f"[PAGINATION] Handling pagination for {base_url}")
        current_page = 1
        initial_height = await page.evaluate('document.body.scrollHeight')

        while current_page <= self.max_pagination_pages:
            await extract_links_fn(soup)  # Extract product links from current page
            # print(f"[COUNT] Found {len(self.all_product_links)} product links on page {current_page}")
            try:
                next_button = None
                if self.pagination_selector_or_text:
                    # Try selector first
                    next_button = await page.query_selector(self.pagination_selector_or_text)
                    if not next_button:
                        # Fallback to text search
                        next_button = await page.query_selector(f"text={self.pagination_selector_or_text}")

                if not next_button:
                    # print("[PAGINATION] No next button found. Ending pagination.")
                    break

                # Click and wait for content change
                prev_url = page.url
                await next_button.click()
                await page.wait_for_timeout(3000)  # Wait for navigation/DOM change
                await page.wait_for_load_state("domcontentloaded")
                current_height = await page.evaluate('document.body.scrollHeight')
                # if page.url == prev_url:
                #     print("[PAGINATION] URL did not change. Possibly end of pages.")
                #     break

                if current_height == initial_height:
                    break

                # Parse new content
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                current_page += 1

            except Exception as e:
                # print(f"[PAGINATION ERROR] Failed on page {current_page}: {e}")
                break
        await extract_links_fn(soup)

    async def block_static_resources(self, page):
        # Block unnecessary static files like images
        await page.route("**/*.{png,jpg,jpeg,svg,woff,woff2,ttf}", lambda route: route.abort())


    async def scrape(self):
        async with async_playwright() as p:
            # browser = await p.chromium.launch(headless=False, slow_mo=100)
            start_time = time.time()
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
            

            semaphore = asyncio.Semaphore(20)  # Limit to 5 concurrent tabs

            # Crawl queue and visited set
            to_crawl = [self.domain]
            tasks = []

            async def crawl_with_semaphore(url, depth):
                async with semaphore:
                    page = await context.new_page()
                    await self.block_static_resources(page)
                    try:
                        await crawl(url, depth, page)
                    finally:
                        await page.close()

            async def crawl(url, depth, page):
                if depth > 4 or url in self.visited_urls:
                    return
                self.visited_urls.add(url)

                try:
                    await page.goto(url, timeout=60000, wait_until='domcontentloaded')

                    # Handle popup
                    if depth < 2:
                        try:
                            await page.click(f'button:has-text("{self.pop_up_text}")', timeout=5000)
                            # print("[MODAL] Closed popup.")
                        except Exception as e:
                            # print(f"[ERROR] Couldn't close Popup: {e}")
                            pass

                    # Infinite scroll or pagination
                    if self.infinite_scroll:
                        await self.scroll_to_bottom(page, self.infinite_loader_text)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                    elif self.pagination_selector_or_text and self.max_pagination_pages > 0:
                        async def extract_links(soup):
                            for tag in soup.find_all("a", href=True):
                                href = tag.get("href")
                                if not href:
                                    continue
                                full_url = (
                                    f"https://{self.domain_netloc}{href}"
                                    if href.startswith("/")
                                    else href
                                )
                                if self.is_internal_link(full_url) and self.is_product_url(full_url):
                                    self.all_product_links.add(full_url)

                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        await self.handle_pagination(page, url, soup, extract_links)
                    
                    # content = await page.content()
                    # soup = BeautifulSoup(content, "html.parser")
                    
                    for tag in soup.find_all("a", href=True):
                        href = tag.get("href")
                        if not href:
                            continue
                        full_url = (
                            f"https://{self.domain_netloc}{href}"
                            if href.startswith("/")
                            else href
                        )
                        if not self.is_internal_link(full_url):
                            continue

                        if self.is_product_url(full_url):
                            self.all_product_links.add(full_url)
                        else:
                            to_crawl.append(full_url)

                    print(f"[LINKS] Found {len(self.all_product_links)} product links so far.")

                except Exception as e:
                    print(f"[ERROR] Couldn't visit {url}: {e}")

            # Schedule first layer of URLs
            depth = 0;
            while to_crawl:
                if len(self.all_product_links) >= 5:
                    print(f"[INFO] Found 5 product URLs. Stopping crawl.")
                    break
                # print(to_crawl)
                next_batch = []
                tasks = []
                for url in to_crawl:
                    if url not in self.visited_urls:
                        tasks.append(crawl_with_semaphore(url, depth))
                to_crawl = next_batch
                await asyncio.gather(*tasks)
                depth+= 1
                # break  # Remove this if you want deep recursion

            await browser.close()
            end_time = time.time()
            time_taken = (end_time - start_time) / 60
            print(f"[INFO] Total time taken: {time_taken:.2f} minutes")
            print(f"[DONE] Total unique product links found: {len(self.all_product_links)}.")
            return list(self.all_product_links)


