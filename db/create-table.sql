-- this is for creating a table if there is none. There will likely be none until you get a persistent database going another time.
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