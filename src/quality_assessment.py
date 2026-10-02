from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed" / "hcmc_poi.parquet"
OUTPUT_PATH = ROOT / "data" / "processed" / "hcmc_poi_quality.parquet"


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    text_fields = ["name", "address", "phone", "website", "opening_hours", "category"]
    for field in text_fields:
        if field not in out.columns:
            out[field] = ""

    out["name_missing"] = out["name"].apply(lambda x: clean_text(x) == "")
    out["address_missing"] = out["address"].apply(lambda x: clean_text(x) == "")
    out["category_missing"] = out["category"].apply(lambda x: clean_text(x) == "")
    out["phone_missing"] = out["phone"].apply(lambda x: clean_text(x) == "")
    out["website_missing"] = out["website"].apply(lambda x: clean_text(x) == "")
    out["hours_missing"] = out["opening_hours"].apply(lambda x: clean_text(x) == "")

    out["invalid_latitude"] = out["latitude"].apply(lambda x: pd.isna(x) or not (-90 <= float(x) <= 90) if pd.notna(x) else True)
    out["invalid_longitude"] = out["longitude"].apply(lambda x: pd.isna(x) or not (-180 <= float(x) <= 180) if pd.notna(x) else True)
    out["invalid_geo"] = out["invalid_latitude"] | out["invalid_longitude"]

    out["issue_count"] = (
        out["name_missing"].astype(int)
        + out["address_missing"].astype(int)
        + out["category_missing"].astype(int)
        + out["phone_missing"].astype(int)
        + out["website_missing"].astype(int)
        + out["hours_missing"].astype(int)
        + out["invalid_geo"].astype(int)
    )

    penalty_map = {
        "name_missing": 15,
        "address_missing": 20,
        "category_missing": 15,
        "phone_missing": 5,
        "website_missing": 5,
        "hours_missing": 5,
        "invalid_geo": 25,
    }

    out["quality_score"] = 100
    for key, penalty in penalty_map.items():
        out["quality_score"] = out["quality_score"] - out[key].astype(int) * penalty

    out["quality_score"] = out["quality_score"].clip(lower=0, upper=100)

    out["quality_grade"] = pd.cut(
        out["quality_score"],
        bins=[-1, 39, 69, 84, 100],
        labels=["Poor", "Fair", "Good", "Excellent"],
        right=True,
    )

    return out


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_parquet(INPUT_PATH)
    quality_df = build_quality_report(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    quality_df.to_parquet(OUTPUT_PATH, index=False)

    summary = {
        "records": len(quality_df),
        "avg_quality_score": round(float(quality_df["quality_score"].mean()), 2),
        "poor_quality": int((quality_df["quality_grade"] == "Poor").sum()),
        "fair_quality": int((quality_df["quality_grade"] == "Fair").sum()),
        "good_quality": int((quality_df["quality_grade"] == "Good").sum()),
        "excellent_quality": int((quality_df["quality_grade"] == "Excellent").sum()),
        "missing_name": int(quality_df["name_missing"].sum()),
        "missing_address": int(quality_df["address_missing"].sum()),
        "missing_category": int(quality_df["category_missing"].sum()),
        "invalid_geo": int(quality_df["invalid_geo"].sum()),
    }

    print("Quality report created:")
    for key, value in summary.items():
        print(f"- {key}: {value}")

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
