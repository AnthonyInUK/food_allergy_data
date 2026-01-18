import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'data/food_data.db')


def clean_and_consolidate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("开始执行数据审计与安全合并...")

    # 1. 找出重复的条形码
    cursor.execute("""
        SELECT barcode, COUNT(*) as c 
        FROM products 
        WHERE barcode IS NOT NULL 
        GROUP BY barcode 
        HAVING c > 1
    """)
    duplicates = cursor.fetchall()
    print(f"发现 {len(duplicates)} 组条形码重复的产品。")

    for barcode, count in duplicates:
        # 获取这组重复产品的所有记录
        cursor.execute(
            "SELECT id, name, ingredients, image_url, allergens FROM products WHERE barcode = ?", (barcode,))
        records = cursor.fetchall()

        # 挑选“信息最全”的一条作为主记录
        # 优先级：有图片 > 配料表长 > 有原始过敏原标签
        main_record = sorted(records, key=lambda x: (
            1 if x[3] else 0,
            len(x[2]) if x[2] else 0,
            1 if x[4] else 0
        ), reverse=True)[0]

        main_id = main_record[0]
        other_ids = [r[0] for r in records if r[0] != main_id]

        # 安全合并逻辑：将其他重复记录的过敏原映射全部迁移到主记录 ID 下
        # 这样即使 A 记录写了 soy，B 记录写了 peanut，合并后主记录会拥有全部过敏原
        for old_id in other_ids:
            cursor.execute(
                "UPDATE OR IGNORE allergen_mappings SET product_id = ? WHERE product_id = ?", (main_id, old_id))
            cursor.execute("DELETE FROM products WHERE id = ?", (old_id,))

    conn.commit()

    # 2. 清理完全没有名字或配料的“垃圾数据”
    cursor.execute(
        "DELETE FROM products WHERE (name IS NULL OR name = '') AND (ingredients IS NULL OR ingredients = '')")
    deleted_junk = cursor.rowcount

    conn.commit()
    conn.close()
    print(f"清理完成：合并了重复条码，删除了 {deleted_junk} 条无效记录。")


if __name__ == "__main__":
    clean_and_consolidate()
