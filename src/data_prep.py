import os
import pandas as pd

# Base directory setup
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_and_clean(filename="NCRB_Table_1A.1.csv"):
    file_path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(file_path)

    # --- Standardize column names ---
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^\w_]", "", regex=True)  # remove special chars like ()
    )

    # --- Rename important fields if present ---
    rename_map = {
        "stateut": "state_ut",
        "midyear_projected_population_in_lakhs_2022": "population_lakhs",
        "rate_of_cognizable_crimes_ipc_2022": "crime_rate_ipc_2022",
        "chargesheeting_rate_2022": "chargesheeting_rate_2022"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # --- Identify year columns dynamically (numeric column names like 2020, 2021, 2022, etc.) ---
    year_cols = [c for c in df.columns if c.isdigit()]

    # --- Reshape wide → long format ---
    id_vars = [c for c in ["state_ut", "population_lakhs", "crime_rate_ipc_2022", "chargesheeting_rate_2022"] if c in df.columns]
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=year_cols,
        var_name="year",
        value_name="total_crimes"
    )

    # --- Clean data types ---
    df_long["year"] = df_long["year"].astype(int)
    df_long["total_crimes"] = pd.to_numeric(df_long["total_crimes"], errors="coerce")
    if "population_lakhs" in df_long.columns:
        df_long["population_lakhs"] = pd.to_numeric(df_long["population_lakhs"], errors="coerce")
    if "crime_rate_ipc_2022" in df_long.columns:
        df_long["crime_rate_ipc_2022"] = pd.to_numeric(df_long["crime_rate_ipc_2022"], errors="coerce")
    if "chargesheeting_rate_2022" in df_long.columns:
        df_long["chargesheeting_rate_2022"] = pd.to_numeric(df_long["chargesheeting_rate_2022"], errors="coerce")

    # --- Drop rows without state or crime values ---
    df_long = df_long.dropna(subset=["state_ut", "total_crimes"])

    return df_long
