import asyncio
from crawler.manager import CrawlerManager
from crawler.writer import save_results
# from crawler.playwright_scraper import PlaywrightScraper
from crawler.playwright_scraper2 import PlaywrightScraper
from domains import domains

async def main():
    # Step 1: Load domains
    # with open("domains.txt", "r") as f:
    #     domains = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(domains)} domains to crawl...")

    # Step 2: Initialize the Crawler Manager
    manager = CrawlerManager(domains=domains)
    
    # Step 3: Start crawling using aiohttp + BS
    results = await manager.run_all()

    # Step 4: Fallback to Playwright if any domain returned 0 product URLs
    for domain in domains:
        if domain in results and len(results[domain]) == 0:
            print(f"[FALLBACK] Trying Playwright for {domain}...")
            scraper = PlaywrightScraper(domain)
            try:
                alt_results = await scraper.scrape()
                if alt_results:
                    results[domain].extend(alt_results)
            except Exception as e:
                print(f"[FALLBACK ERROR] Playwright failed for {domain}: {e}")

    # Step 5: Output the results
    save_results(results)
    print("Crawling complete. Product URLs saved.")


if __name__ == "__main__":
    asyncio.run(main())
