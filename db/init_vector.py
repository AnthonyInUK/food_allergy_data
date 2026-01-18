import sqlite3
import chromadb
from chromadb.utils import embedding_functions
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/food_data.db')
CHROMA_PATH = os.path.join(os.path.dirname(__file__), '../data/chroma_db')


def init_vector_db():
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Use a default embedding function (e.g., SentenceTransformer)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2")

    collection = client.get_or_create_collection(
        name="food_products",
        embedding_function=sentence_transformer_ef
    )

    # Connect to SQLite to get data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, brand, ingredients, allergens FROM products")
    rows = cursor.fetchall()

    all_documents = []
    all_metadatas = []
    all_ids = []

    for row in rows:
        p_id, name, brand, ingredients, allergens = row
        doc_text = f"Name: {name or ''}. Brand: {brand or ''}. Ingredients: {ingredients or ''}. Allergens: {allergens or ''}."

        all_documents.append(doc_text)
        all_metadatas.append({
            "id": p_id,
            "name": name or "",
            "brand": brand or "",
            "allergens": allergens or ""
        })
        all_ids.append(p_id)

    # Process in batches to avoid ChromaDB limits (max ~5461)
    batch_size = 1000
    total = len(all_documents)

    if total > 0:
        print(f"开始同步 {total} 条数据到向量库...")
        for i in range(0, total, batch_size):
            batch_docs = all_documents[i:i + batch_size]
            batch_metas = all_metadatas[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]

            collection.upsert(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            print(f"   进度: {min(i + batch_size, total)} / {total}")

        print(f"成功将 {total} 条产品索引到向量数据库。")

    conn.close()


if __name__ == "__main__":
    init_vector_db()
