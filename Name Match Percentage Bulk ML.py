import pandas as pd
import numpy as np
import re
from itertools import combinations
from difflib import SequenceMatcher
from typing import Optional

# ---------------------------
# CONFIG
# ---------------------------
INPUT_FILE = r"C:\Users\anura\Downloads\Operator Property list.xlsx"
SHEET_NAME = 0  # or sheet name
ID_COL = "OYO ID"
NAME_COL = "Operator Name"
OUTPUT_FILE = r"C:\Users\anura\Downloads\name_similarity_output.xlsx"

# ---------------------------
# CLEANING / NORMALIZATION
# ---------------------------
def normalize_text(text: Optional[str]) -> str:
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()

    # remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text

# ---------------------------
# SIMILARITY FUNCTION
# ---------------------------
def similarity(a: str, b: str) -> float:
    if not a and not b:
        return 100.0
    if not a or not b:
        return 0.0

    return round(SequenceMatcher(None, a, b).ratio() * 100, 2)

# ---------------------------
# CORE LOGIC
# ---------------------------
def compute_pairwise(df: pd.DataFrame) -> pd.DataFrame:
    results = []

    # normalize once (vectorized)
    df["_norm_name"] = df[NAME_COL].apply(normalize_text)

    grouped = df.groupby(ID_COL, dropna=False)

    for group_id, group in grouped:
        names = group["_norm_name"].tolist()
        raw_names = group[NAME_COL].tolist()

        # skip if only 1 entry
        if len(names) < 2:
            continue

        # generate combinations (nC2)
        for (i, j) in combinations(range(len(names)), 2):
            sim = similarity(names[i], names[j])

            results.append({
                ID_COL: group_id,
                "name_1": raw_names[i],
                "name_2": raw_names[j],
                "similarity_percent": sim
            })

    return pd.DataFrame(results)

# ---------------------------
# MAIN
# ---------------------------
def main():
    try:
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

        # basic validation
        if ID_COL not in df.columns or NAME_COL not in df.columns:
            raise ValueError(f"Missing required columns: {ID_COL}, {NAME_COL}")

        # drop completely empty rows
        df = df[[ID_COL, NAME_COL]].dropna(how="all")

        result_df = compute_pairwise(df)

        # sort for readability
        result_df = result_df.sort_values(
            by=[ID_COL, "similarity_percent"],
            ascending=[True, False]
        )

        result_df.to_excel(OUTPUT_FILE, index=False)

        print(f"Done. Output saved to: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()