import requests
import zipfile
import io
import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')
# 更新后的 Health Canada CNF 2015 下载链接
CNF_URL = "https://www.canada.ca/content/dam/hc-sc/documents/services/food-nutrition/healthy-eating/nutrient-data/canadian-nutrient-file-2015-download-files/cnf-fce-2015-csv.zip"


def download_and_extract():
    print(f"正在从 Health Canada 下载数据: {CNF_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(CNF_URL, headers=headers, timeout=60)
        if response.status_code == 200:
            z = zipfile.ZipFile(io.BytesIO(response.content))
            os.makedirs("data/temp_cnf", exist_ok=True)
            z.extractall("data/temp_cnf")
            print("下载并解压完成。")
            return "data/temp_cnf"
        else:
            print(f"下载失败: 状态码 {response.status_code}")
            return None
    except Exception as e:
        print(f"网络异常: {e}")
        return None


def process_cnf(folder_path):
    print(f"正在处理目录中的官方数据: {folder_path}")

    # 尝试寻找食品名称文件，处理可能的文件名差异
    # 手动下载的版本通常叫 "FOOD NAME.csv"，自动下载的版本可能叫 "FOOD_NM.csv"
    possible_names = ["FOOD NAME.csv", "FOOD_NM.csv"]
    df_food = None

    for name in possible_names:
        file_path = os.path.join(folder_path, name)
        if os.path.exists(file_path):
            print(f"找到数据文件: {file_path}")
            try:
                df_food = pd.read_csv(file_path, encoding="ISO-8859-1")
                break
            except Exception as e:
                print(f"尝试读取 {name} 时出错: {e}")

    if df_food is None:
        print(f"错误：在 {folder_path} 中找不到有效的食品名称文件 (FOOD NAME.csv 或 FOOD_NM.csv)")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        count = 0
        for _, row in df_food.iterrows():
            # 不同的 CSV 版本列名可能略有不同，做兼容处理
            food_id = row.get('FoodID') or row.get('FoodId')
            desc_en = row.get('FoodDescription') or row.get('FoodName')
            desc_fr = row.get('FoodDescriptionF') or row.get('FoodNameF')

            if not food_id or not desc_en:
                continue

            data = (
                f"CNF_{food_id}",
                'CNF',
                None,
                desc_en,
                "Health Canada",
                f"{desc_en} / {desc_fr}",  # 存入双语名称
                None,
                None,
                None,
                "Standard Canadian Food",
                "Canada"
            )

            cursor.execute('''
                INSERT OR REPLACE INTO products (id, source, barcode, name, brand, ingredients, allergens, traces, image_url, categories, countries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            count += 1

        conn.commit()
        conn.close()
        print(f"成功从 CNF 导入 {count} 条标准食品数据。")

    except Exception as e:
        print(f"处理数据时出错: {e}")


if __name__ == "__main__":
    # 优先检查用户手动下载的目录
    manual_dir = "cnf-fcen-csv"
    temp_dir = "data/temp_cnf"

    if os.path.exists(manual_dir):
        process_cnf(manual_dir)
    elif os.path.exists(temp_dir):
        process_cnf(temp_dir)
    else:
        # 如果都没有，尝试自动下载
        downloaded_path = download_and_extract()
        if downloaded_path:
            process_cnf(downloaded_path)
        else:
            print("无法获取 CNF 数据。请手动下载并解压到 cnf-fcen-csv 文件夹。")
