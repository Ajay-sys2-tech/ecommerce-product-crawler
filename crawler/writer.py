import json
import os
from datetime import datetime

def save_results(results, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"product_urls_{timestamp}.json")

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Saved product URLs to: {output_file}")
    _print_summary(results)

def _print_summary(results):
    print("\n--- Crawl Summary ---")
    for domain, urls in results.items():
        print(f"{domain}: {len(urls)} product URLs")
    print("---------------------\n")
