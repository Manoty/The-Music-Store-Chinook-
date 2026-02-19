import sqlite3
import pandas as pd
import requests
import os

# 1. Setup directories
os.makedirs('seeds', exist_ok=True)

# 2. Downloading the actual SQLite file from the repo 
url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
db_path = "chinook.sqlite"

print("Downloading Chinook database...")
r = requests.get(url)
with open(db_path, 'wb') as f:
    f.write(r.content)

# 3. Connecting and exporting each table to CSV
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']

print(f"Found {len(tables)} tables. Exporting to seeds/...")

for table in tables:
    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    # Saving to CSV (dbt seed requires .csv extension)
    df.to_csv(f"seeds/{table}.csv", index=False)
    print(f"  - Created seeds/{table}.csv")

conn.close()
os.remove(db_path) # Cleaning up the sqlite file
print("\nDone! You can now run 'dbt seed'.")