
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from site_configs import SITE_CONFIGS

class PlaywrightScraper:
    def __init__(self, domain):
        self.domain = domain
        self.product_patterns = SITE_CONFIGS.get(domain, {}).get("product_url_patterns", [])
        self.infinite_scroll = SITE_CONFIGS.get(domain, {}).get("infinite_scroll", False)

        self.domain_netloc = urlparse(domain).netloc
        self.visited_urls = set()
        self.all_product_links = set()

        self.pagination_selector_or_text = SITE_CONFIGS.get(domain, {}).get("pagination_selector_or_text")
        self.max_pagination_pages = SITE_CONFIGS.get(domain, {}).get("max_pagination_pages", 0)

    def is_internal_link(self, url):
        return urlparse(url).netloc == "" or urlparse(url).netloc == self.domain_netloc


    def is_product_url(self, url):
        for pattern in self.product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    async def scroll_to_bottom(self, page, loading_selector_or_text=None):
        print(f"[SCROLL] Starting smart scroll...")

        seen_heights = set()
        scroll_count = 0

        while True and scroll_count < 100:
            scroll_count += 1
            try:
                # STEP 1: Try to find the loading element by selector or inner text
                loading_element = None

                if loading_selector_or_text:
                    # First try direct selector
                    loading_element = await page.query_selector(loading_selector_or_text)

                    # If not found, try text-based matching
                    if not loading_element:
                        print(f"[SEARCH] Trying to find element with text: {loading_selector_or_text}")
                        loading_element = await page.query_selector(f"text={loading_selector_or_text}")
                    
                    if not loading_element:
                        print(f"[SEARCH] Trying to find element with text: {'Loading'}")
                        loading_element = await page.query_selector(f"text={'Loading'}")

                if not loading_element:
                    print("[LOADING] Loading element not found, assuming end of content.")
                    break

                # STEP 2: Scroll the loading element into view
                await loading_element.scroll_into_view_if_needed()
                print("[SCROLL] Scrolled loading element into view.")

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
                        print(f"[HEIGHT] New content loaded: {new_height}")
                        break
                    waited += interval
                else:
                    print("[TIMEOUT] No new content detected.")

                # STEP 4: Track page height to know when we're done
                current_height = await page.evaluate('document.body.scrollHeight')
                print(f"[HEIGHT] Current page height: {current_height}")
                if current_height in seen_heights:
                    print("[END] No new content detected after scroll.")
                    break
                seen_heights.add(current_height)

            except Exception as e:
                print(f"[ERROR] Scrolling or waiting failed: {e}")
                break

    async def handle_pagination(self, page, base_url, soup, extract_links_fn):
        print(f"[PAGINATION] Starting pagination crawl (Max pages: {self.max_pagination_pages})")
        current_page = 1
        initial_height = await page.evaluate('document.body.scrollHeight')

        while current_page <= self.max_pagination_pages:
            print(f"[PAGINATION] On page {current_page}")
            extract_links_fn(soup)  # Extract product links from current page

            try:
                next_button = None
                if self.pagination_selector_or_text:
                    # Try selector first
                    next_button = await page.query_selector(self.pagination_selector_or_text)
                    if not next_button:
                        # Fallback to text search
                        print(f"[PAGINATION] Searching for button with text '{self.pagination_selector_or_text}'")
                        next_button = await page.query_selector(f"text={self.pagination_selector_or_text}")

                if not next_button:
                    print("[PAGINATION] 'Next' button not found. Ending pagination.")
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
                    print("[PAGINATION] Page height did not change. Possibly end of pages.")
                    break

                # Parse new content
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                current_page += 1

            except Exception as e:
                print(f"[PAGINATION ERROR] Failed on page {current_page}: {e}")
                break

    
    async def scrape(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=100)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            async def crawl(url, depth):
                if depth > 4 or url in self.visited_urls:
                    return
                print(f"[DEPTH {depth}] Visiting: {url}")
                self.visited_urls.add(url)

                try:
                    await page.goto(url, timeout=60000, wait_until='domcontentloaded')

                      # Close popup/modal
                    try:
                        await page.wait_for_selector('button:has-text("Ask Me Later")', timeout=5000)
                        await page.click('button:has-text("Ask Me Later")')
                        print("[MODAL] Closed 'Ask Me Later' popup.")
                    except:
                        print("[MODAL] No popup or couldn't close it.")

                    # Scroll to load more content (if applicable)
                    if self.infinite_scroll:
                        print("[SCROLL] Infinite scroll detected. Scrolling...") 
                        await self.scroll_to_bottom(page, 'Load More')
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
                                    print(f"[PRODUCT] Found (paginated): {full_url}")
                                    self.all_product_links.add(full_url)

                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        await self.handle_pagination(page, url, soup, extract_links)

                    # content = await page.content()
                    # soup = BeautifulSoup(content, "html.parser")

                    print(f"[COUNT] Found {len(soup.find_all("a", href=True))} product links so far.")
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

                        # Save product links if applicable
                        if self.is_product_url(full_url):
                            print(f"[PRODUCT] Found: {full_url}")
                            self.all_product_links.add(full_url)

                        # Recurse deeper
                        else:
                            await crawl(full_url, depth + 1)

                except Exception as e:
                    print(f"[ERROR] Couldn't visit {url}: {e}")

            try:
                await crawl(self.domain, depth=1)
            finally:
                await browser.close()

            print(f"[DONE] Total unique product links found: {len(self.all_product_links)}")
            return list(self.all_product_links)