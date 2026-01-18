import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')
JAPAN_EXCEL = os.path.join(os.path.dirname(
    __file__), '../data/japan_standard_foods.xlsx')

CATEGORY_MAP = {
    "01": "Grains (穀類)",
    "02": "Potatoes and Starches (いも及びでん粉類)",
    "03": "Sugars and Sweeteners (砂糖及び甘味類)",
    "04": "Pulses (豆類)",
    "05": "Nuts and Seeds (種実類)",
    "06": "Vegetables (野菜類)",
    "07": "Fruits (果実類)",
    "08": "Mushrooms (きのこ類)",
    "09": "Algae (藻類)",
    "10": "Seafood (魚介類)",
    "11": "Meat (肉類)",
    "12": "Eggs (鶏卵類)",
    "13": "Milk and Dairy (乳類)",
    "14": "Fats and Oils (油脂類)",
    "15": "Confectionery (菓子類)",
    "16": "Beverages (し好飲料類)",
    "17": "Seasonings and Spices (調味料及び香辛料類)",
    "18": "Prepared Foods (調理済み流通食品類)"
}


def process_japan_official():
    if not os.path.exists(JAPAN_EXCEL):
        print(f"Error: {JAPAN_EXCEL} not found.")
        return

    print(f"Processing Japan Standard Food Composition Table (2020)...")

    try:
        # 读取 '表全体' sheet，不使用表头，手动处理
        df = pd.read_excel(JAPAN_EXCEL, sheet_name='表全体', header=None)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        count = 0
        # 数据从第 11 行开始 (index 11)
        for i in range(11, len(df)):
            row = df.iloc[i]

            # 列 1: 食品番号, 列 3: 食品名
            food_no = str(row[1]).strip()
            name_jp = str(row[3]).strip()

            # 验证数据有效性
            if not food_no or food_no == 'nan' or len(food_no) < 5:
                continue
            if not name_jp or name_jp == 'nan':
                continue

            # 提取分类 (前两位)
            cat_code = food_no[:2]
            category = CATEGORY_MAP.get(cat_code, "Other")

            food_id = f"JPN_{food_no}"

            data = (
                food_id,
                'JPN_GOV',
                None,
                name_jp,
                "MEXT Japan",
                name_jp,  # Ingredients
                None,
                None,
                None,
                category,
                "Japan"
            )

            cursor.execute('''
                INSERT OR REPLACE INTO products (id, source, barcode, name, brand, ingredients, allergens, traces, image_url, categories, countries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            count += 1

        conn.commit()
        conn.close()
        print(f"成功从日本官方数据导入 {count} 条标准食材记录。")

    except Exception as e:
        print(f"处理数据时出错: {e}")


if __name__ == "__main__":
    process_japan_official()
