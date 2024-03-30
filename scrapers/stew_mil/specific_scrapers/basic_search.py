from ..stew_mil_base_class import StewMilBase

class StewMilBasicScraper(StewMilBase):
    def __init__(self, db_handler):
        super().__init__(db_handler)
        self.search_url = self.config['search_url']

    def scrape(self):
        print("Scraping in the basic_search.py file...")
        start_page = 1
        while True:
            full_url = f"{self.base_url}{self.search_url.format(page=start_page)}"
            soup = self.send_request(full_url)
            if soup is None:
                print("Failed to retrieve data or max retries reached, ending scraper.")
                break

            products = soup.select(self.product_selectors['product_container'])
            if not products:
                print("No more products found, ending scraper.")
                break
            else:
                print(f"Found {len(products)} products on page {start_page}")

            for product in products:
                self.process_product(product)

            start_page += 1

    def process_product(self, product):
        super().process_product(product)  # Assuming process_product is defined in StewMilBase
