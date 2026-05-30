import sqlite3
import pandas as pd

input_data = 'data/forum.db'

def load_data():
    conn = sqlite3.connect(input_data)
    data = pd.read_sql_query("SELECT * FROM inceldom", conn)
    conn.close()
    return data

df = load_data()

pickle_path = "data/forum_raw.pkl"
df.to_pickle(pickle_path)
print(f"Saved: '{pickle_path}' ({len(df)} entries)")

json_path = "data/forum_raw.json"
df.to_json(json_path, orient="records", lines=True, date_format="iso")
print(f"Saved: '{json_path}' ({len(df)} entries)")