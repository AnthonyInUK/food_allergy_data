CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    source TEXT, -- 'OFF' or 'USDA'
    barcode TEXT,
    name TEXT,
    brand TEXT,
    ingredients TEXT,
    allergens TEXT,
    traces TEXT,
    image_url TEXT,
    categories TEXT,
    countries TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS allergen_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT,
    allergen_name TEXT,
    status TEXT, -- 'contains', 'may_contain', 'traces'
    FOREIGN KEY (product_id) REFERENCES products(id)
);

