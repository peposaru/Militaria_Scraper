-- This script is for creating the products table if it does not already exist.
CREATE TABLE IF NOT EXISTS products (
    url VARCHAR(255),
    product_id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    price NUMERIC(10, 2),
    product_thumbnail TEXT,
    images TEXT,
    status VARCHAR(50),
    data_enter_date DATE
);