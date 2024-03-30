from ..stew_mil_base_class import StewMilBase

class StewMilNewItemsScraper(StewMilBase):
    def __init__(self, db_handler):
        super().__init__(db_handler)
        self.new_item_url = self.config['new_item_url']

    def scrape(self):
        print("Scraping new items...")
        currentRow = 0
        while True:
            full_url = f"{self.base_url}{self.archive_url.format(currentRow=currentRow)}"
            soup = self.send_request(full_url)
            if soup is None:
                print("Failed to retrieve data or max retries reached, ending scraper.")
                break

            products = soup.select(self.product_selectors['product_container'])
            if not products:
                print("No archive products found, ending scraper.")
                break

            for product in products:
                self.process_product(product)

            currentRow += 50

    def process_product(self, product):
        super().process_product(product) 