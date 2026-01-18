import sqlite3
import pandas as pd
import os

# 获取项目根目录 (相对于 db/export_csv.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data/food_data.db')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data/food_products_summary.csv')


def export_to_csv():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        print("Please run this script from the project root or ensure scripts/fetch_off.py has run.")
        return

    print("Exporting data to CSV...")
    conn = sqlite3.connect(DB_PATH)

    # 1. 获取所有产品基本信息
    query_products = "SELECT id, barcode, name, brand, source, ingredients, countries FROM products"
    df_products = pd.read_sql_query(query_products, conn)

    # 2. 获取过敏原映射并聚合
    query_allergens = "SELECT product_id, allergen_name, status FROM allergen_mappings"
    df_mappings = pd.read_sql_query(query_allergens, conn)

    if df_mappings.empty:
        df_final = df_products
        df_final['allergens_confirmed'] = ''
        df_final['allergens_may_contain'] = ''
    else:
        # 聚合确切含有的过敏原
        confirmed = df_mappings[df_mappings['status'] == 'contains'].groupby(
            'product_id')['allergen_name'].apply(lambda x: ', '.join(x)).reset_index()
        confirmed.columns = ['id', 'allergens_confirmed']

        # 聚合可能含有的过敏原
        may_contain = df_mappings[df_mappings['status'] == 'may_contain'].groupby(
            'product_id')['allergen_name'].apply(lambda x: ', '.join(x)).reset_index()
        may_contain.columns = ['id', 'allergens_may_contain']

        # 3. 合并数据
        df_final = df_products.merge(confirmed, on='id', how='left').merge(
            may_contain, on='id', how='left')

    # 清洗：将 NaN 替换为空字符串
    df_final = df_final.fillna('')

    # 4. 导出
    df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"Export completed: {OUTPUT_PATH}")
    print(f"Total rows exported: {len(df_final)}")

    conn.close()


if __name__ == "__main__":
    export_to_csv()
