-- schema.sql
-- Schema for the UrbanCart analytics database (SQLite)

DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id         TEXT PRIMARY KEY,
    signup_date          DATE,
    region                TEXT,
    acquisition_channel   TEXT,
    loyalty_score         REAL
);

DROP TABLE IF EXISTS products;
CREATE TABLE products (
    product_id     TEXT PRIMARY KEY,
    category        TEXT,
    unit_price      REAL,
    unit_cost       REAL,
    product_name    TEXT
);

DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id               TEXT PRIMARY KEY,
    customer_id            TEXT REFERENCES customers(customer_id),
    order_date             DATE,
    status                  TEXT,
    region                  TEXT,
    acquisition_channel     TEXT
);

DROP TABLE IF EXISTS order_items;
CREATE TABLE order_items (
    order_id      TEXT REFERENCES orders(order_id),
    product_id    TEXT REFERENCES products(product_id),
    quantity      INTEGER,
    unit_price    REAL,
    unit_cost     REAL
);

DROP TABLE IF EXISTS ab_test_campaign;
CREATE TABLE ab_test_campaign (
    customer_id   TEXT REFERENCES customers(customer_id),
    grp           TEXT,       -- 'control' or 'variant'
    converted     INTEGER,
    order_value   REAL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);
