import aiohttp
from aiohttp import ClientTimeout
from tenacity import retry, stop_after_attempt, wait_fixed

class AsyncFetcher:
    def __init__(self, domain):
        self.domain = domain
        self.timeout = ClientTimeout(total=10)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EcommBot/1.0; +https://shoppin.ai/crawler)"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    async def fetch(self, url):
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200 and 'text/html' in response.headers.get("Content-Type", ""):
                        return await response.text()
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
        return None
