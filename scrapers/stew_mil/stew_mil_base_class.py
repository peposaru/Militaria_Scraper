import json
from ..base_scraper import BaseScraper
import os

class StewMilBase(BaseScraper):
    def __init__(self, db_handler, config_path=os.path.join('scrapers', 'scraper_config.json')):
        super().__init__(db_handler)
        # Load the configuration values from the JSON file
        with open(config_path, 'r') as f:
            self.config = json.load(f)['stew_mil']
        
        self.base_url = self.config['base_url']
        self.product_selectors = self.config['product_selectors']

    def scrape(self):
        # Placeholder for scraper-specific logic to be implemented by subclasses
        raise NotImplementedError("Scrape method must be implemented by subclasses.")
        
    # havent decided if this is should stay in the stew_mil base class or the base class of all scrapers so we don't repeat ourselves. This depends on if the selectors are the same. We can always clean the data with pandas before this step if we need to...
    def process_product(self, product):
        # Extract common product information using the configured selectors
        title = product.select_one(self.product_selectors['title']).get_text(strip=True)
        price = product.select_one(self.product_selectors['price']).get_text(strip=True)
        product_url_suffix = product.select_one(self.product_selectors['url'])['href']
        product_url = f"{self.base_url}{product_url_suffix}" if not product_url_suffix.startswith("http") else product_url_suffix

        # Use the inherited product_id_generator method from BaseScraper
        product_id = self.product_id_generator()

        # Assuming db_handler has a method for safe SQL execution with parameterized queries
        self.db_handler.sql_execute(
            "INSERT INTO products (product_id, title, url, price) VALUES (%s, %s, %s, %s)", 
            (product_id, title, product_url, price)
        )
        
        print(f"Processed {title} with ID {product_id} found at {product_url}")