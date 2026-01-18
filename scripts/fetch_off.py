import requests
import sqlite3
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')


def get_robust_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'FoodDataCollector - Canada - EducationProject (https://github.com/anthony/fooddata)'
    })
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def save_to_db(products):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    for p in products:
        p_id = p.get('_id') or p.get('code')
        if not p_id:
            continue

        ingredients = p.get('ingredients_text') or p.get(
            'ingredients_text_en') or p.get('ingredients_text_fr')
        name = p.get('product_name') or p.get('product_name_en')

        data = (
            str(p_id),
            'OFF',
            p.get('code'),
            name,
            p.get('brands'),
            ingredients,
            p.get('allergens'),
            p.get('traces'),
            p.get('image_url'),
            p.get('categories'),
            p.get('countries')
        )

        cursor.execute('''
            INSERT OR REPLACE INTO products (id, source, barcode, name, brand, ingredients, allergens, traces, image_url, categories, countries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        count += 1

    conn.commit()
    conn.close()
    return count


def fetch_by_category_robust(session, category_tag, max_pages=None):
    page = 1
    total_in_cat = 0
    print(f"\n[开始扫描分类] 标签: {category_tag}")

    while True:
        if max_pages and page > max_pages:
            print(f"   - 已达到该分类设定的最大页数 ({max_pages})，跳过。")
            break

        url = f"https://world.openfoodfacts.org/category/{category_tag}/{page}.json"

        try:
            response = session.get(url, timeout=30)
            if response.status_code == 404:
                break
            if response.status_code != 200:
                page += 1
                continue

            data = response.json()
            products = data.get('products', [])
            if not products:
                break

            saved = save_to_db(products)
            total_in_cat += saved
            print(f"   [页码 {page}] 成功保存 {saved} 条记录 (累计: {total_in_cat})")

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"   - 异常: {e}")
            time.sleep(5)
            continue


def fetch_by_origin_search(session, origin_name, max_pages=20):
    """
    针对分类标签不全的国家，直接按“产地/起源地”进行搜索
    """
    print(f"\n[开始搜索产地] 起源地: {origin_name}")
    page = 1
    total_in_origin = 0

    while page <= max_pages:
        # 使用搜索接口搜索 origins 字段
        fields = "code,product_name,brands,ingredients_text,allergens,traces,image_url,categories,countries"
        url = f"https://ca.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=origins&tag_contains_0=contains&tag_0={origin_name}&fields={fields}&page_size=100&page={page}&json=true"

        try:
            response = session.get(url, timeout=30)
            if response.status_code != 200:
                break

            data = response.json()
            products = data.get('products', [])

            if not products:
                break

            saved = save_to_db(products)
            total_in_origin += saved
            print(
                f"   [页码 {page}] 产地 {origin_name} 成功抓取 {len(products)} 条，新增/更新 {saved} 条")

            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"   - 异常: {e}")
            break


if __name__ == "__main__":
    session = get_robust_session()

    # 1. 之前抓得比较顺的分类标签（设置 50 页上限，防止卡死）
    safe_tags = [
        "en:dairy-substitutes",
        "en:desserts",
        "en:pickled-foods",
        "en:seaweed-snacks",
        "en:frozen-prepared-meals",
        "en:condiments",
        "en:curry-pastes",
        "en:soups"
    ]

    for tag in safe_tags:
        fetch_by_category_robust(session, tag, max_pages=50)

    # 2. 针对之前失败的国家，使用“产地搜索”暴力增补
    origins = [
        "China", "Japan", "South Korea", "Thailand", "Vietnam",
        "Taiwan", "Philippines", "Malaysia", "Singapore", "India"
    ]

    for origin in origins:
        try:
            fetch_by_origin_search(session, origin, max_pages=20)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"搜索 {origin} 失败: {e}")

    print("\n--- 采集任务全部结束 ---")
