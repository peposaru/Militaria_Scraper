-- This script is for creating the militaria table if it does not already exist when running the scraper.
CREATE TABLE IF NOT EXISTS militaria (
    url VARCHAR(255) PRIMARY KEY,
    title TEXT,
    description TEXT,
    price NUMERIC,
    available BOOLEAN,
    date DATE,
    site TEXT,
    date_sold DATE DEFAULT NULL,
    date_scraped DATE DEFAULT CURRENT_DATE
);
