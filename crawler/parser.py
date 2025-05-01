from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract
import re
from site_configs import SITE_CONFIGS

class URLParser:
    def __init__(self, domain):
        self.domain = domain
        self.domain_netloc = urlparse(domain).netloc
        self.domain_base = tldextract.extract(domain).registered_domain
        self.product_patterns = SITE_CONFIGS.get(domain, {}).get("product_url_patterns", [])

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            full_url = urljoin(base_url, href)

            if full_url.startswith("http"):
                links.add(full_url)

        return links

    def is_product_url(self, url):
        # Check if the URL matches any known product pattern
        for pattern in self.product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def is_same_domain(self, url):
        # Make sure we're not crawling external links
        parsed = tldextract.extract(url)
        return parsed.registered_domain == self.domain_base
