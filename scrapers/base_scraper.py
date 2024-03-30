import requests
from bs4 import BeautifulSoup
import time

class BaseScraper:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def send_request(self, url, retries=3, backoff_factor=0.3):
        """Send a GET request to a URL, with specified retries and backoff factor."""
        for attempt in range(retries):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"Request to {url} successful.")
                    time.sleep(3)
                    return BeautifulSoup(response.content, 'html.parser')
                else:
                    print(f"Request to {url} failed with status code {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Request to {url} failed with error: {e}")
                time.sleep(backoff_factor * (2 ** attempt))
        return None

    def product_id_generator(self):
        """Generate a new product ID based on the maximum ID present in the database."""
        last_product_id = self.db_handler.sql_fetch('''SELECT MAX(product_id) FROM products''')
        if last_product_id and last_product_id[0][0] is not None:
            return int(last_product_id[0][0]) + 1
        else:
            return 1

    def scrape(self):
        """Placeholder method for the scraping logic to be implemented by derived classes."""
        raise NotImplementedError("This method should be overridden by derived classes.")
