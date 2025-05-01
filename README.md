🕷️ E-Commerce Product URL Crawler
This is an asynchronous web crawler designed to extract product page URLs from major fashion e-commerce websites.

It uses a hybrid strategy:

First, it attempts to crawl using aiohttp + BeautifulSoup for speed.

If no product URLs are found, it falls back to Playwright for JS-rendered content (e.g., infinite scroll or pagination).

📦 Features
🔍 Domain-specific configurations for handling different website structures.

⚡ Asynchronous crawling with depth control.

🧠 Fallback with Playwright for dynamic content and JavaScript-heavy pages.

🔗 Extracts valid internal product URLs based on regex patterns.

📄 Saves crawl results in JSON with timestamps.

🔒 Respects domain limits and uses a user-agent header.

📁 Project Structure
```
.
├── crawler/
│   ├── fetcher.py          # Async HTTP fetcher using aiohttp
│   ├── manager.py          # Manages the crawling process
│   ├── parser.py           # Parses HTML and extracts links
│   ├── playwright_scraper2.py # JS-enabled fallback scraper using Playwright
│   └── writer.py           # Saves results and prints summaries
├── site_configs.py         # Regex and crawling strategies for each site
├── domains.py              # List of domains to crawl
├── main.py                 # Entry point
└── output/                 # Output folder with timestamped result JSONs
```

🚀 How to Run
1. Install Dependencies
```bash
pip install -r requirements.txt
```
You’ll also need to install Playwright and its browser binaries:

```bash
playwright install
```
2. Run the Crawler
```bash
python main.py
```



