import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data/food_data.db')

# 1. 定义品牌映射字典（可根据需要持续添加）
BRAND_MAPPING = {
    r"lee kum kee|李錦記|李锦记": "Lee Kum Kee",
    r"nissin|日清食品|日清": "Nissin",
    r"nongshim|农心|農心": "Nongshim",
    r"kikkoman|万字|萬字": "Kikkoman",
    r"maggi|美极|美極": "Maggi",
    r"indomie|营多": "Indomie",
    r"samyang|三养|三養": "Samyang"
}

def sanitize_text(text):
    if not text: return ""
    # 去除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除多余空格和换行
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_garbage_ingredients(text):
    if not text: return True
    # 如果配料表太短，或者包含常见的“无配料”关键词
    garbage_keywords = ["none", "n/a", "not applicable", "see packaging", "no ingredients"]
    if len(text) < 5: return True
    if text.lower() in garbage_keywords: return True
    return False

def advanced_cleaning():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("开始执行高级数据清洗...")

    # 获取所有需要处理的产品
    cursor.execute("SELECT id, name, brand, ingredients FROM products")
    products = cursor.fetchall()
    
    cleaned_count = 0
    garbage_deleted = 0
    
    for p_id, name, brand, ingredients in products:
        new_name = sanitize_text(name)
        new_ingredients = sanitize_text(ingredients)
        new_brand = sanitize_text(brand)
        
        # 1. 品牌归一化
        for pattern, canonical_name in BRAND_MAPPING.items():
            if re.search(pattern, new_brand, re.IGNORECASE) or re.search(pattern, new_name, re.IGNORECASE):
                new_brand = canonical_name
                break
        
        # 2. 检查配料表是否有效
        if is_garbage_ingredients(new_ingredients):
            # 标记这些产品的配料表为 NULL，避免 Agent 被误导
            new_ingredients = ""
            
        # 3. 更新数据库
        cursor.execute("""
            UPDATE products 
            SET name = ?, brand = ?, ingredients = ? 
            WHERE id = ?
        """, (new_name, new_brand, new_ingredients, p_id))
        cleaned_count += 1

    conn.commit()
    
    # 4. 物理删除：删除既没名字又没配料表的完全无用数据
    cursor.execute("DELETE FROM products WHERE (name = '' OR name IS NULL) AND (ingredients = '' OR ingredients IS NULL)")
    garbage_deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"清洗任务完成：")
    print(f" - 标准化/清洗了 {cleaned_count} 条记录")
    print(f" - 删除了 {garbage_deleted} 条完全无效的记录")

if __name__ == "__main__":
    advanced_cleaning()

