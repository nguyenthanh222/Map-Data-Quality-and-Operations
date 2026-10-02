from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "hcmc_poi_quality.parquet"
OUTPUT_PATH = ROOT / "data" / "processed" / "hcmc_poi_deduped.parquet"


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def build_name_address_key(row):
    name = normalize_text(row.get("name"))
    address = normalize_text(row.get("address"))
    category = normalize_text(row.get("category"))
    key = f"{name}|{address}|{category}"
    return key if key else "__missing__"


def build_geo_key(row):
    try:
        lat = float(row.get("latitude", 0) or 0)
        lon = float(row.get("longitude", 0) or 0)
        return round(lat, 5), round(lon, 5)
    except (TypeError, ValueError):
        return (-9999, -9999)


def dedupe_by_name_and_address(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["name_address_key"] = df.apply(build_name_address_key, axis=1)
    df["quality_score"] = pd.to_numeric(df.get("quality_score", 100), errors="coerce").fillna(0)

    df = df.sort_values(["quality_score", "osm_id"], ascending=[False, True])
    deduped = df.drop_duplicates(subset=["name_address_key"], keep="first")
    return deduped.drop(columns=["name_address_key"], errors="ignore")


def dedupe_by_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["geo_key"] = df.apply(build_geo_key, axis=1)
    df = df.sort_values(["quality_score", "osm_id"], ascending=[False, True])
    deduped = df.drop_duplicates(subset=["geo_key"], keep="first")
    return deduped.drop(columns=["geo_key"], errors="ignore")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}. Run quality_check.py first.")

    df = pd.read_parquet(INPUT_PATH)
    name_address_deduped = dedupe_by_name_and_address(df)
    final_df = dedupe_by_coordinates(name_address_deduped)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Original records: {len(df):,}")
    print(f"Deduplicated records: {len(final_df):,}")
    print(f"Removed: {len(df) - len(final_df):,}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
