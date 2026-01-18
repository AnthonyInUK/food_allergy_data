import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')

ALLERGEN_DICT = {
    "en:peanuts": ["peanut", "groundnut", "花生", "落花生", "ピーナッツ", "arachide", "cacahuète"],
    "en:soybeans": ["soy", "soya", "soybean", "lecithin", "大豆", "だいず", "酱油", "醬油", "soja", "edamame", "tofu", "豆豉", "腐乳", "味噌", "miso"],
    "en:milk": ["milk", "dairy", "whey", "casein", "lactose", "牛奶", "乳", "牛乳", "脱脂粉乳", "lait", "cheese", "yogurt", "cream", "butter", "奶油", "奶粉", "芝士", "炼乳", "condensed milk"],
    "en:eggs": ["egg", "albumen", "yolk", "鸡蛋", "卵", "鶏卵", "œuf", "oeuf", "mayonnaise", "蛋黄"],
    "en:wheat": ["wheat", "gluten", "flour", "小麦", "小麦粉", "blé", "farine de blé", "semolina", "couscous", "面粉", "麩質"],
    "en:fish": ["fish", "bonito", "mackerel", "tuna", "鱼", "魚", "鰹", "サバ", "poisson", "anchovy", "sardine", "salmon", "鱼露", "fish sauce", "鰹節"],
    "en:crustaceans": ["shrimp", "prawn", "crab", "lobster", "虾", "蟹", "エビ", "カニ", "crevette", "crabe", "crustacé", "虾酱", "shrimp paste"],
    "en:tree-nuts": ["almond", "walnut", "cashew", "hazelnut", "pistachio", "坚果", "核桃", "アーモンド", "くるみ", "noix", "amande", "macadamia", "pecan", "腰果", "开心果"],
    "en:sesame-seeds": ["sesame", "芝麻", "ごま", "胡麻", "sésame", "tahini", "麻油"],
    "en:molluscs": ["mollusc", "oyster", "squid", "octopus", "clam", "mussel", "scallop", "蚝", "蚝油", "oyster sauce", "鱿鱼", "章鱼", "扇贝", "蛤蜊"],
    "en:mustard": ["mustard", "芥末", "芥子", "moutarde", "wasabi"],
    "en:buckwheat": ["buckwheat", "soba", "荞麦", "蕎麦", "そば", "sarrasin"],
    "en:sulphites": ["sulphite", "sulfite", "sulfur dioxide", "dioxyde de soufre", "二氧化硫", "亚硫酸盐", "亜硫酸塩", "e220", "e221", "e222", "e223", "e224", "e225", "e226", "e227", "e228"],
    "en:celery": ["celery", "céleri", "芹菜", "セロリ"],
    "en:lupin": ["lupin", "羽扇豆", "ルピナス"],
    "en:barley": ["barley", "orge", "大麦", "大麥", "おおむぎ", "malt", "麦芽"]
}

MAY_CONTAIN_PHRASES = [
    "may contain", "may also contain", "produced in a facility",
    "processed on equipment", "traces of", "可能含有", "可能包含",
    "本产品生产线也处理", "含微量"
]


def enrich_allergens():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("正在清理旧的过敏原映射数据...")
    cursor.execute("DELETE FROM allergen_mappings")

    cursor.execute("SELECT id, ingredients, allergens, traces FROM products")
    products = cursor.fetchall()

    print(f"正在重新处理 {len(products)} 个产品...")

    added_count = 0
    for p_id, ingredients, api_allergens, api_traces in products:
        found_allergens = {}

        if api_allergens:
            for a in [a.strip() for a in api_allergens.split(',') if a.strip()]:
                found_allergens[a] = "contains"

        if api_traces:
            for t in [t.strip() for t in api_traces.split(',') if t.strip()]:
                if t not in found_allergens:
                    found_allergens[t] = "may_contain"

        if ingredients:
            ing_lower = ingredients.lower()
            main_part = ing_lower
            may_part = ""
            for phrase in MAY_CONTAIN_PHRASES:
                if phrase in ing_lower:
                    parts = ing_lower.split(phrase, 1)
                    main_part = parts[0]
                    may_part = parts[1]
                    break

            for tag, keywords in ALLERGEN_DICT.items():
                if found_allergens.get(tag) == "contains":
                    continue
                if any(kw.lower() in main_part for kw in keywords):
                    found_allergens[tag] = "contains"
                    continue
                if any(kw.lower() in may_part for kw in keywords):
                    found_allergens[tag] = "may_contain"

        for tag, status in found_allergens.items():
            cursor.execute("INSERT INTO allergen_mappings (product_id, allergen_name, status) VALUES (?, ?, ?)",
                           (p_id, tag, status))
            added_count += 1

    conn.commit()
    conn.close()
    print(f"处理完成！当前数据库共有 {added_count} 条唯一的过敏原关系。")


if __name__ == "__main__":
    enrich_allergens()
