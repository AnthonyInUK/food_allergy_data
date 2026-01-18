import sqlite3
import json
import os

DB_PATH = 'data/food_data.db'
GRAPH_OUTPUT = 'data/food_graph.jsonl'

def build_graph():
    if not os.path.exists(DB_PATH):
        print("SQL 数据库不存在")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 提取产品与过敏原的关系
    cursor.execute("""
        SELECT p.name, m.allergen_name, m.status 
        FROM products p 
        JOIN allergen_mappings m ON p.id = m.product_id
    """)
    
    graph_data = []
    for row in cursor.fetchall():
        product_name, allergen, status = row
        # 构建图关系：(产品) -[含有/可能含有]-> (过敏原)
        relation = {
            "subject": product_name,
            "predicate": "contains" if status == 'contains' else "may_contain",
            "object": allergen
        }
        graph_data.append(relation)

    # 存入文件
    with open(GRAPH_OUTPUT, 'w', encoding='utf-8') as f:
        for entry in graph_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"图数据已生成至 {GRAPH_OUTPUT}，共 {len(graph_data)} 条关系。")
    conn.close()

if __name__ == "__main__":
    build_graph()

