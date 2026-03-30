import json
import re
from itertools import combinations
from difflib import SequenceMatcher
from typing import Optional, Dict, Any
from urllib import request, error

import pandas as pd

# ---------------------------
# CONFIG
# ---------------------------
INPUT_FILE = r"C:\Users\anura\Downloads\Operator Property list.xlsx"
SHEET_NAME = 0  # or sheet name
ID_COL = "OYO ID"
NAME_COL = "Operator Name"
OUTPUT_FILE = r"C:\Users\anura\Downloads\name_similarity_output_ollama.xlsx"

SEQ_THRESHOLD = 50.0
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:latest"
OLLAMA_TIMEOUT_SECONDS = 90

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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(text[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

    return None


def ollama_name_rating(name_1: str, name_2: str, seq_similarity: float) -> Dict[str, Any]:
    prompt = (
        "You are a strict name-matching fraud screening assistant. "
        "Compare two person names and decide if they represent the same person name pattern. "
        "Possible status must be only: match or no_match. "
        "Return valid JSON only with keys: status, match_percent, reason. "
        "match_percent must be a number 0 to 100. "
        "Keep reason short.\n\n"
        f"Name 1: {name_1}\n"
        f"Name 2: {name_2}\n"
        f"SequenceMatcher similarity: {seq_similarity}\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0
        }
    }

    req = request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            root = json.loads(body)
            llm_response_text = root.get("response", "")

            parsed = _extract_json_object(llm_response_text) or {}

            status = str(parsed.get("status", "no_match")).strip().lower()
            if status not in {"match", "no_match"}:
                status = "no_match"

            llm_percent = round(max(0.0, min(100.0, _safe_float(parsed.get("match_percent"), seq_similarity))), 2)
            reason = str(parsed.get("reason", ""))[:300]

            return {
                "llm_status": status,
                "llm_match_percent": llm_percent,
                "llm_reason": reason,
                "llm_error": ""
            }

    except error.URLError as e:
        return {
            "llm_status": "no_match",
            "llm_match_percent": seq_similarity,
            "llm_reason": "",
            "llm_error": f"Ollama connection error: {e}"
        }
    except Exception as e:
        return {
            "llm_status": "no_match",
            "llm_match_percent": seq_similarity,
            "llm_reason": "",
            "llm_error": f"Ollama parse/runtime error: {e}"
        }

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

            if sim < SEQ_THRESHOLD:
                continue

            llm_result = ollama_name_rating(raw_names[i], raw_names[j], sim)

            results.append({
                ID_COL: group_id,
                "name_1": raw_names[i],
                "name_2": raw_names[j],
                "sequence_similarity_percent": sim,
                "llm_status": llm_result["llm_status"],
                "llm_match_percent": llm_result["llm_match_percent"],
                "llm_reason": llm_result["llm_reason"],
                "llm_error": llm_result["llm_error"]
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

        if result_df.empty:
            print(f"No pairs found with sequence similarity >= {SEQ_THRESHOLD}%")
            return

        # sort for readability
        result_df = result_df.sort_values(
            by=[ID_COL, "sequence_similarity_percent", "llm_match_percent"],
            ascending=[True, False]
        )

        result_df.to_excel(OUTPUT_FILE, index=False)

        print(f"Done. Output saved to: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()