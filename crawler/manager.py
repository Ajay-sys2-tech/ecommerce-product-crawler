import asyncio
from crawler.fetcher import AsyncFetcher
from crawler.parser import URLParser

class CrawlerManager:
    def __init__(self, domains):
        self.domains = domains
        self.results = {}

        self.visited = set()
        self.product_urls = set()
        self.max_depth = 3

    async def crawl_domain(self, url, domain, depth=0, max_depth=3, visited=None, product_urls=None):
        if visited is None:
            visited = set()
        if product_urls is None:
            product_urls = set()
        if(len(self.product_urls) >= 50):
            print(f"[INFO] Found 50 product URLs. Stopping crawl.")
            return product_urls
        # Base case: Stop if we've reached max depth or visited this URL
        if url in visited or depth > max_depth:
            return product_urls

        # Add the URL to the visited set
        visited.add(url)

        # Fetch the page content
        fetcher = AsyncFetcher(domain)
        parser = URLParser(domain)

        html = await fetcher.fetch(url)
        if not html:
            print(f"[SKIP] No HTML or fetch failed: {url}")
            return product_urls

        # Extract links from the page
        links = parser.extract_links(html, base_url=url)

        # Process each link
        for link in links:
            if parser.is_same_domain(link):
                if parser.is_product_url(link):
                    # If it's a product URL, add it to the product_urls set
                    if 'www.' not in link:
                        link = 'https://www.' + link.split('//')[1]
                    product_urls.add(link)
                    # if len(product_urls) >= 50:
                    #     print(f"[INFO] Found 50 product URLs. Stopping crawl.")
                    #     return product_urls
                else:
                    # Otherwise, recursively crawl this link
                    await self.crawl_domain(link, domain, depth + 1, max_depth, visited, product_urls)

        return product_urls


    async def run_all(self):
        tasks = [self.crawl_domain(domain, domain) for domain in self.domains]
        results = await asyncio.gather(*tasks)
        # return dict(results) #for non recursive function
        # return {domain: product_urls for domain, product_urls in zip(self.domains, results)}
        return {domain: list(product_urls) for domain, product_urls in zip(self.domains, results)}
