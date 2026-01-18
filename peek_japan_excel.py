import pandas as pd


def peek_excel(file_path):
    print(f"Peeking into: {file_path}")
    # Read first 20 rows to understand the header structure
    try:
        df = pd.read_excel(file_path, nrows=20)
        print("\n--- First 20 rows (raw) ---")
        print(df.to_string())

        # Check sheet names
        xl = pd.ExcelFile(file_path)
        print(f"\nSheet names: {xl.sheet_names}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    peek_excel("data/japan_standard_foods.xlsx")
