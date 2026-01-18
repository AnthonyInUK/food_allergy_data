import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')

def check_data_quality():
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== Data Correctness & Consistency Audit ===\n")

    # 1. Basic Counts
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    print(f"Total products: {total_products}")

    # 2. Duplicate Check
    cursor.execute("SELECT barcode, COUNT(*) as count FROM products WHERE barcode IS NOT NULL GROUP BY barcode HAVING count > 1")
    duplicates = cursor.fetchall()
    print(f"Duplicate barcodes found: {len(duplicates)}")
    if duplicates:
        print(f"   (Top 5 duplicates: {duplicates[:5]})")

    # 3. Completeness Check
    cursor.execute("SELECT COUNT(*) FROM products WHERE name IS NULL OR name = ''")
    missing_name = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE ingredients IS NULL OR ingredients = ''")
    missing_ingredients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE brand IS NULL OR brand = ''")
    missing_brand = cursor.fetchone()[0]

    print(f"\nCompleteness:")
    print(f" - Missing Name: {missing_name} ({missing_name/total_products:.1%})")
    print(f" - Missing Ingredients: {missing_ingredients} ({missing_ingredients/total_products:.1%})")
    print(f" - Missing Brand: {missing_brand} ({missing_brand/total_products:.1%})")

    # 4. Consistency: Foreign Key Integrity
    cursor.execute("""
        SELECT COUNT(*) FROM allergen_mappings 
        WHERE product_id NOT IN (SELECT id FROM products)
    """)
    orphaned_mappings = cursor.fetchone()[0]
    print(f"\nConsistency:")
    print(f" - Orphaned allergen mappings (no matching product): {orphaned_mappings}")

    # 5. Redundancy Check: Same allergen marked as both contains and may_contain for same product
    cursor.execute("""
        SELECT product_id, allergen_name, COUNT(DISTINCT status) as status_count 
        FROM allergen_mappings 
        GROUP BY product_id, allergen_name 
        HAVING status_count > 1
    """)
    redundant_logic = cursor.fetchall()
    print(f" - Products with redundant allergen logic (both contains & may_contain): {len(redundant_logic)}")

    # 6. Source Distribution
    cursor.execute("SELECT source, COUNT(*) FROM products GROUP BY source")
    sources = cursor.fetchall()
    print(f"\nSource Distribution: {dict(sources)}")

    # 7. Sample check for specific Asian flags
    cursor.execute("SELECT COUNT(*) FROM products WHERE categories LIKE '%asian%' OR categories LIKE '%chinese%' OR categories LIKE '%japanese%'")
    asian_flagged = cursor.fetchone()[0]
    print(f"\nAsian Food Coverage:")
    print(f" - Products with Asian-related keywords in categories: {asian_flagged} ({asian_flagged/total_products:.1%})")

    conn.close()

if __name__ == "__main__":
    check_data_quality()

