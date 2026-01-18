import sqlite3
import os
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = 'data/food_data.db'
CHROMA_PATH = 'data/chroma_db'


def inspect_sqlite():
    print("\n=== 1. 验证数据一致性 (查看含有 Traces 的产品) ===")
    if not os.path.exists(DB_PATH):
        print("SQLite 数据库文件不存在")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查找有 traces 信息的 3 个产品
    cursor.execute("""
        SELECT id, name, brand, ingredients, traces 
        FROM products 
        WHERE traces IS NOT NULL AND traces != '' 
        LIMIT 3
    """)
    rows = cursor.fetchall()

    if not rows:
        print("数据库中暂无带有 Traces 标记的产品，正在展示普通产品...")
        cursor.execute(
            "SELECT id, name, brand, ingredients, traces FROM products WHERE ingredients IS NOT NULL LIMIT 3")
        rows = cursor.fetchall()

    for row in rows:
        p_id, name, brand, ingredients, traces = row
        print(f"【产品】: {name} ({brand})")
        print(f"【原文成分】: {ingredients}" if ingredients else "【原文成分】: 无")
        print(f"【原文 Traces】: {traces}" if traces else "【原文 Traces】: 无")

        # 查找该产品关联的所有标签
        cursor.execute(
            "SELECT allergen_name, status FROM allergen_mappings WHERE product_id = ? ORDER BY status, allergen_name", (p_id,))
        mappings = cursor.fetchall()
        print("【已识别标签】:")
        if not mappings:
            print("   -> (未识别出过敏原)")
        for m_name, m_status in mappings:
            status_str = "确认含有" if m_status == 'contains' else "可能含有"
            print(f"   -> {m_name:20} | {status_str}")
        print("-" * 60)

    # 2. 查看所有过敏原完整统计
    cursor.execute("""
        SELECT allergen_name, status, COUNT(*) as count 
        FROM allergen_mappings 
        GROUP BY allergen_name, status 
        ORDER BY count DESC
        LIMIT 20
    """)
    print("\n=== 2. 全库过敏原统计 (Top 20) ===")
    rows = cursor.fetchall()
    if not rows:
        print("- 暂无过敏原数据")
    for row in rows:
        name, status, count = row
        status_str = "确切含有" if status == 'contains' else "可能含有"
        print(f"- {name:25} | {status_str}: {count} 个产品")

    conn.close()


def inspect_vector_db():
    print("\n=== 向量数据库 (ChromaDB) 状态 ===")
    if not os.path.exists(CHROMA_PATH):
        print("向量数据库目录不存在")
        return

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # 使用与 init_vector.py 相同的模型
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2")
    collection = client.get_collection(
        name="food_products", embedding_function=ef)

    count = collection.count()
    print(f"向量库中已索引产品数: {count}")

    if count > 0:
        # 尝试做一个简单的语义搜索
        query = "Asian noodle with soy sauce"
        print(f"\n测试语义搜索: '{query}'")
        results = collection.query(query_texts=[query], n_results=3)

        for i in range(len(results['ids'][0])):
            print(
                f"匹配 {i+1}: {results['metadatas'][0][i]['name']} (来自: {results['metadatas'][0][i]['brand']})")


if __name__ == "__main__":
    inspect_sqlite()
    inspect_vector_db()
