import sqlite3
import pandas as pd

input_data = "data/forum.db"
activity_formats = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y",
)

def load_data():
    conn = sqlite3.connect(input_data)
    data = pd.read_sql_query("SELECT * FROM inceldom", conn)
    conn.close()
    return data

def parse_latest_activity(values):
    """Parse current timestamp-based and legacy date-only activity values."""
    parsed_values = pd.Series(
        pd.NaT,
        index=values.index,
        dtype="datetime64[ns, UTC]",
    )

    for activity_format in activity_formats:
        missing_values = parsed_values.isna() & values.notna()
        if not missing_values.any():
            break

        parsed_values.loc[missing_values] = pd.to_datetime(
            values.loc[missing_values],
            format=activity_format,
            errors="coerce",
            utc=True,
        )

    return parsed_values

def sort_by_latest_activity(data):
    """Sort forum rows by newest thread activity first."""
    if "latest_activity" not in data.columns:
        return data

    latest_activity = parse_latest_activity(data["latest_activity"])

    return (
        data.assign(_latest_activity_sort=latest_activity)
        .sort_values(
            by="_latest_activity_sort",
            ascending=False,
            na_position="last",
            kind="mergesort",
        )
        .drop(columns="_latest_activity_sort")
        .reset_index(drop=True)
    )

def main():
    df = sort_by_latest_activity(load_data())

    pickle_path = "data/forum_raw.pkl"
    df.to_pickle(pickle_path)
    print(f"Saved: '{pickle_path}' ({len(df)} entries)")

    json_path = "data/forum_raw.json"
    df.to_json(json_path, orient="records", lines=True, date_format="iso")
    print(f"Saved: '{json_path}' ({len(df)} entries)")

if __name__ == "__main__":
    main()