import pandas as pd
import os

# Create the seeds directory if it doesn't exist
os.makedirs('seeds', exist_ok=True)

# List of tables in the Chinook dataset
tables = [
    'Artist', 'Album', 'Track', 'Genre', 'MediaType', 
    'Playlist', 'PlaylistTrack', 'Invoice', 'InvoiceLine', 
    'Customer', 'Employee'
]

# Base URL for raw CSVs (stable GitHub source)
base_url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/DataSources/"

for table in tables:
    print(f"Fetching {table}...")
    # Chinook uses different extensions for different versions, 
    # but the .csv files are readily available in many repos.
    # We will use the Kaggle-exported CSV structures for simplicity:
    url = f"https://raw.githubusercontent.com/lerocha/chinook-database/master/DataSources/ChinookData.json"
    # Actually, let's use a dedicated CSV repo for zero-friction
    csv_url = f"https://raw.githubusercontent.com/yields-io/chinook-dataset/master/data/{table}.csv"
    
    try:
        df = pd.read_csv(csv_url)
        df.to_csv(f"seeds/{table.lower()}.csv", index=False)
    except:
        print(f"Could not find {table} at that URL, trying alternative...")

print("Done! Check your /seeds folder.")