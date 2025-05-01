SITE_CONFIGS = {
    "https://www.tatacliq.com/": {
        "product_url_patterns": [r"/[a-z0-9\-]+/p-[a-z0-9]+",],
        "infinite_scroll": False,
        "pagination_selector_or_text": "Show More Products",
        "max_pagination_pages": 10,
         "pop_up_text": "Ask Me Later",
    },
    "https://www.nykaafashion.com/": {
        "product_url_patterns": [r"/[a-z0-9\-]+/p/[a-z0-9]+",],
        "infinite_scroll": True,
        "pop_up_text": "No thanks",
        "infinite_loader_text": ['Load More', 'Loading'],
    },
    "https://www.virgio.com/": {
        "product_url_patterns": [ r"/products/\w+", ],
    },
    "https://www.westside.com/": {
        "product_url_patterns": [r"/products/[a-z0-9\-]+",],
    },
    "https://www.myntra.com/": {
        "product_url_patterns": [r"/[a-z0-9]+/[a-z0-9]+/[a-z0-9\-]+/[0-9]{8}/buy",],
        "infinite_scroll": False,
        "pagination_selector_or_text": "Next",
        "max_pagination_pages": 10
    },
}
