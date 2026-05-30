import requests
import time
import random
from scraper.config import agent, min_d, max_d, timeout, retry_attempts, retry_backoff

class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": agent})

    def get_html(self, url):
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
        
        for attempt in range(1, retry_attempts + 1):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.content
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                if not self._should_retry_status(status_code):
                    print(f"Network error with URL: {url}: {e}")
                    return None
                self._wait_before_retry(url, e, attempt)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                self._wait_before_retry(url, e, attempt)
            except requests.exceptions.RequestException as e:
                print(f"Network error with URL: {url}: {e}")
                return None

        return None

    @staticmethod
    def _should_retry_status(status_code):
        return status_code == 429 or (status_code is not None and 500 <= status_code < 600)

    def _wait_before_retry(self, url, error, attempt):
        if attempt >= retry_attempts:
            print(f"Network error with URL: {url}: {error}")
            return

        wait_time = retry_backoff * (2 ** (attempt - 1)) + random.uniform(0, retry_backoff)
        print(
            f"Network error with URL: {url}: {error}. "
            f"Retrying {attempt + 1}/{retry_attempts} in {wait_time:.1f}s..."
        )
        time.sleep(wait_time)