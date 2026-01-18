# food_allergy_data

A data pipeline to collect and process food ingredient data for allergy detection. It pulls from multiple sources, standardizes the data into SQLite, and generates vector embeddings for semantic search.

## Data Sources
- **Open Food Facts**: Bulk scanning of Asian food categories and origins.
- **USDA FoodData Central**: Branded and foundation foods.
- **Health Canada (CNF)**: Official Canadian food nutrient data (English/French).
- **Japan MEXT**: Standard tables for Japanese ingredient mapping.

## Structure
- `scripts/`: Python scripts for fetching data from each API/source.
- `db/`: Database setup, SQL schema, allergen enrichment, and export logic.
- `data/`: Local storage for SQLite and ChromaDB (ignored by git).
- `run_pipeline.py`: Main entry point to run the full collection process.

## Setup
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Add your USDA API key to a `.env` file:
   ```text
   USDA_API_KEY=your_api_key_here
   ```
3. Run the pipeline:
   ```bash
   python run_pipeline.py
   ```

## Workflow
1. **Fetch**: Run scripts in `scripts/` to populate `food_data.db`.
2. **Clean**: 
   - `db/advanced_cleaning.py`: Normalizes brand names (e.g., merging "李錦記" and "Lee Kum Kee") and sanitizes ingredient text.
   - `db/clean_data.py`: Deduplicates products by barcode and merges fragmented data from different sources (Data Coalescence).
3. **Enrich**: Run `db/enrich_allergens.py` to tag allergens across English, French, Chinese, and Japanese.
4. **Index**: Run `db/init_vector.py` to sync SQL data to the vector store.
5. **Export**: Run `db/export_csv.py` to generate a shareable CSV summary.

## Data Quality Strategy
To ensure the reliability of the knowledge base for AI Agent reasoning, the pipeline implements a multi-stage refinement process:
- **Normalizing Entities**: Uses regex-based brand mapping to resolve entity ambiguity across multi-lingual sources.
- **Data Coalescence**: Instead of simple deletion, the pipeline merges duplicate records by prioritizing the most complete ingredient lists while preserving unique metadata (images, external tags) from secondary sources.
- **Heuristic Filtering**: Automatically identifies and strips "garbage" text (e.g., "See packaging", "N/A") from ingredient lists to prevent RAG hallucination.
- **Conflict Resolution**: Implements a "Safety-First" policy where confirmed allergens take precedence over "may contain" traces during merging.

## Output
- `data/food_data.db`: Full SQLite database (local only).
- `data/chroma_db`: Vector database for AI retrieval (local only).
- `data/food_products_summary.csv`: Exported summary of products and detected allergens (tracked in git).
