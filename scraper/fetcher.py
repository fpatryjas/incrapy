import requests
import time
import random
from scraper.config import agent, min_d, max_d

class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": agent})

    def get_html(self, url):
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Network error with URL: {url}: {e}")
            return None