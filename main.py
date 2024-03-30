import sys
from scrapers.stew_mil.specific_scrapers.basic_search import StewMilBasicScraper
from scrapers.stew_mil.specific_scrapers.archive import StewMilArchiveScraper
from scrapers.stew_mil.specific_scrapers.new_items import StewMilNewItemsScraper
from database_handler import PostgreSQLProcessor
import os

def main(scraper_type):
    # Database connection parameters
    host_name = os.getenv("DATABASE_HOST", "localhost")
    database_name = os.getenv("DATABASE_NAME", "stew_mil_db")
    user_name = os.getenv("DATABASE_USER", "postgres")
    password = os.getenv("DATABASE_PASSWORD", "poop")
    port = int(os.getenv("DATABASE_PORT", 5432))

    db_handler = PostgreSQLProcessor(host_name, database_name, user_name, password, port)
    db_handler.connect_with_retry()

    # Map scraper_type to the corresponding class
    scrapers = {
        "basic": StewMilBasicScraper,
        "archive": StewMilArchiveScraper,
        "new": StewMilNewItemsScraper
    }

    scraper_class = scrapers.get(scraper_type)
    if not scraper_class:
        print(f"Unknown scraper type provided: {scraper_type}")
        db_handler.sql_close()
        return

    # Instantiate the scraper and start scraping
    scraper = scraper_class(db_handler)
    scraper.scrape()

    # Close the database connection
    db_handler.sql_close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <scraper_type>")
        print("scraper_type: basic, archive, new")
    else:
        main(sys.argv[1])
