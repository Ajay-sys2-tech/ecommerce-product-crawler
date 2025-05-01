# 🕷️ E-Commerce Product URL Crawler #

This is an asynchronous web crawler designed to extract product page URLs from major fashion e-commerce websites.

It uses a hybrid strategy:

- First, it attempts to crawl using aiohttp + BeautifulSoup for speed.

- If no product URLs are found, it falls back to Playwright for JS-rendered content (e.g., infinite scroll or pagination).

📦 Features

- 🔍 Domain-specific configurations for handling different website structures.

- ⚡ Asynchronous crawling with depth control.

- 🧠 Fallback with Playwright for dynamic content and JavaScript-heavy pages.

- 🔗 Extracts valid internal product URLs based on regex patterns.

- 📄 Saves crawl results in JSON with timestamps.

- 🔒 Respects domain limits and uses a user-agent header.

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


🧠 Strategy: Product URL Discovery

The crawler uses a two-tier strategy to efficiently discover product URLs while minimizing resource usage and handling both static and dynamic content.

1. Primary Crawl (Fast, Static Parsing)
  - Uses aiohttp + BeautifulSoup to fetch and parse raw HTML.
  
  - Extracts all &lt;a href="..."&gt; links from each page.
  
  - Filters links using:
  
    - Domain match (tldextract ensures the link belongs to the same base domain).
  
    - Regex-based pattern match (product_url_patterns) defined in site_configs.py.
  
  - If product URLs are found, the crawler stops here and writes the result.

2. Fallback Crawl (Playwright for JS-rendered Pages)
If the primary crawl doesn't find any valid product URLs for a domain, the crawler switches to a dynamic scraping strategy using Playwright:

- Key Components:
  - Headless Browser Automation to render JavaScript-heavy sites.
    
  - Handling Infinite Scroll:
    - Repeatedly scrolls to the bottom.
    - Waits for elements like "Loading..." to disappear before continuing.
      
  - Handling Pagination:
    - Clicks "Next" or "Show More" buttons using either CSS selectors or inner text.
    - Repeats up to a configured page limit (max_pagination_pages).

- Additional Features:
    - Popup Handling: Automatically clicks away modals using known text like "Ask Me Later".
    - Resource Optimization: Blocks heavy static files (images, fonts) during scraping.
    - Depth-Limited Crawling: Stops recursion after a certain depth to avoid infinite loops.



