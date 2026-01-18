import requests
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')
API_KEY = os.getenv('USDA_API_KEY', 'DEMO_KEY')

def save_to_db(foods):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for f in foods:
        fdc_id = f.get('fdcId')
        if not fdc_id: continue
        cursor.execute('''
            INSERT OR REPLACE INTO products (id, source, barcode, name, brand, ingredients, image_url, categories, countries)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(fdc_id), 'USDA', f.get('gtinUpc'), f.get('description'), f.get('brandOwner'), f.get('ingredients'), None, f.get('foodCategory'), 'United States'))
    conn.commit()
    conn.close()

def fetch_usda_bulk(queries=['Asian', 'Chinese', 'Japanese', 'Korean', 'Thai']):
    for query in queries:
        for page in range(1, 11): # 每个关键词抓 10 页
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={API_KEY}&query={query}&pageSize=100&pageNumber={page}&dataType=Branded"
            print(f"Fetching USDA {query} page {page}...")
            try:
                response = requests.get(url, timeout=20)
                data = response.json()
                foods = data.get('foods', [])
                if not foods: break
                save_to_db(foods)
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    fetch_usda_bulk()
