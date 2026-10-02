from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "hcmc_poi_deduped.parquet"
ENRICHED_OUTPUT = ROOT / "data" / "processed" / "hcmc_poi_enriched.parquet"
SUMMARY_PATH = ROOT / "data" / "processed" / "poi_analytics_summary.csv"
GROUP_PATH = ROOT / "data" / "processed" / "poi_category_by_area.csv"

CATEGORY_ALIASES = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "coffee": "cafe",
    "coffee shop": "cafe",
    "bakery": "restaurant",
    "food": "restaurant",
    "fast food": "restaurant",
    "biergarten": "restaurant",
    "pub": "restaurant",
    "bar": "restaurant",
    "hotel": "hotel",
    "motel": "hotel",
    "guest house": "hotel",
    "pharmacy": "pharmacy",
    "clinic": "healthcare",
    "hospital": "healthcare",
    "doctors": "healthcare",
    "school": "education",
    "college": "education",
    "university": "education",
    "bank": "bank",
    "atm": "bank",
    "fuel": "fuel",
    "gas station": "fuel",
    "gas_station": "fuel",
    "market": "market",
    "supermarket": "market",
    "grocery": "market",
    "mall": "retail",
    "shop": "retail",
    "clothes": "retail",
    "fashion": "retail",
    "department store": "retail",
    "place of worship": "place_of_worship",
    "church": "place_of_worship",
    "temple": "place_of_worship",
    "mosque": "place_of_worship",
    "parking": "parking",
    "bus station": "transport",
    "train station": "transport",
    "airport": "transport",
    "park": "park",
    "playground": "park",
    "library": "services",
    "post office": "services",
    "police": "services",
    "fire station": "services",
    "community centre": "services",
    "community_center": "services",
    "unknown": "unknown",
}

DISTRICT_ALIASES = {
    "q1": "Quận 1",
    "quan 1": "Quận 1",
    "quận 1": "Quận 1",
    "district 1": "Quận 1",
    "q 1": "Quận 1",
    "q2": "Quận 2",
    "quan 2": "Quận 2",
    "quận 2": "Quận 2",
    "district 2": "Quận 2",
    "q3": "Quận 3",
    "quan 3": "Quận 3",
    "quận 3": "Quận 3",
    "district 3": "Quận 3",
    "q4": "Quận 4",
    "quan 4": "Quận 4",
    "quận 4": "Quận 4",
    "district 4": "Quận 4",
    "q5": "Quận 5",
    "quan 5": "Quận 5",
    "quận 5": "Quận 5",
    "district 5": "Quận 5",
    "q6": "Quận 6",
    "quan 6": "Quận 6",
    "quận 6": "Quận 6",
    "district 6": "Quận 6",
    "q7": "Quận 7",
    "quan 7": "Quận 7",
    "quận 7": "Quận 7",
    "district 7": "Quận 7",
    "q8": "Quận 8",
    "quan 8": "Quận 8",
    "quận 8": "Quận 8",
    "district 8": "Quận 8",
    "q9": "Quận 9",
    "quan 9": "Quận 9",
    "quận 9": "Quận 9",
    "district 9": "Quận 9",
    "q10": "Quận 10",
    "quan 10": "Quận 10",
    "quận 10": "Quận 10",
    "district 10": "Quận 10",
    "q11": "Quận 11",
    "quan 11": "Quận 11",
    "quận 11": "Quận 11",
    "district 11": "Quận 11",
    "q12": "Quận 12",
    "quan 12": "Quận 12",
    "quận 12": "Quận 12",
    "district 12": "Quận 12",
    "binh tan": "Quận Bình Tân",
    "bình tân": "Quận Bình Tân",
    "tan tan": "Quận Bình Tân",
    "binh thanh": "Quận Bình Thạnh",
    "bình thạnh": "Quận Bình Thạnh",
    "thu duc": "Quận Thủ Đức",
    "thủ đức": "Quận Thủ Đức",
    "go vap": "Quận Gò Vấp",
    "gò vấp": "Quận Gò Vấp",
    "phu nhuan": "Quận Phú Nhuận",
    "phú nhuận": "Quận Phú Nhuận",
    "tan phu": "Quận Tân Phú",
    "tân phú": "Quận Tân Phú",
    "tan binh": "Quận Tân Bình",
    "tân bình": "Quận Tân Bình",
    "binh chanh": "Huyện Bình Chánh",
    "bình chánh": "Huyện Bình Chánh",
    "can gio": "Huyện Cần Giờ",
    "cần giơ": "Huyện Cần Giờ",
    "cu chi": "Huyện Củ Chi",
    "củ chi": "Huyện Củ Chi",
    "hoc mon": "Huyện Hóc Môn",
    "hóc môn": "Huyện Hóc Môn",
}

WARD_ALIASES = {
    "p1": "Phường 1",
    "phuong 1": "Phường 1",
    "phường 1": "Phường 1",
    "ward 1": "Phường 1",
    "p2": "Phường 2",
    "phuong 2": "Phường 2",
    "phường 2": "Phường 2",
    "ward 2": "Phường 2",
    "p3": "Phường 3",
    "phuong 3": "Phường 3",
    "phường 3": "Phường 3",
    "ward 3": "Phường 3",
    "p4": "Phường 4",
    "phuong 4": "Phường 4",
    "phường 4": "Phường 4",
    "ward 4": "Phường 4",
    "p5": "Phường 5",
    "phuong 5": "Phường 5",
    "phường 5": "Phường 5",
    "ward 5": "Phường 5",
    "p6": "Phường 6",
    "phuong 6": "Phường 6",
    "phường 6": "Phường 6",
    "ward 6": "Phường 6",
    "p7": "Phường 7",
    "phuong 7": "Phường 7",
    "phường 7": "Phường 7",
    "ward 7": "Phường 7",
    "p8": "Phường 8",
    "phuong 8": "Phường 8",
    "phường 8": "Phường 8",
    "ward 8": "Phường 8",
    "p9": "Phường 9",
    "phuong 9": "Phường 9",
    "phường 9": "Phường 9",
    "ward 9": "Phường 9",
    "p10": "Phường 10",
    "phuong 10": "Phường 10",
    "phường 10": "Phường 10",
    "ward 10": "Phường 10",
    "p11": "Phường 11",
    "phuong 11": "Phường 11",
    "phường 11": "Phường 11",
    "ward 11": "Phường 11",
    "p12": "Phường 12",
    "phuong 12": "Phường 12",
    "phường 12": "Phường 12",
    "ward 12": "Phường 12",
}


def normalize_category(value):
    if pd.isna(value):
        return "unknown"

    text = str(value).strip().lower()
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    if not text:
        return "unknown"

    if text in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[text]

    for alias, normalized in CATEGORY_ALIASES.items():
        if alias in text:
            return normalized

    return text.replace(" ", "_")


def title_case_vietnamese(value):
    value = re.sub(r"\s+", " ", str(value).strip())
    if not value:
        return "Unknown"

    parts = value.replace("-", " ").split()
    formatted = []
    for part in parts:
        low = part.lower()
        if low in {"q", "p", "t", "h"}:
            formatted.append(part.upper())
        else:
            formatted.append(part.capitalize())
    return " ".join(formatted)


def map_alias(value, alias_map):
    if pd.isna(value):
        return "Unknown"

    text = str(value).strip().lower()
    if not text:
        return "Unknown"

    normalized = re.sub(r"\s+", " ", text)
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace(".", "")
    normalized = normalized.replace("-", " ")

    if normalized in alias_map:
        return alias_map[normalized]

    for alias, canonical in alias_map.items():
        if alias in normalized:
            return canonical

    return "Unknown"


def normalize_place_label(value, entity):
    if pd.isna(value):
        return "Unknown"

    text = str(value).strip()
    if not text or text.lower() in {"unknown", "na", "n/a"}:
        return "Unknown"

    text = re.sub(r"\s+", " ", text)

    if entity == "district":
        mapped = map_alias(text, DISTRICT_ALIASES)
        if mapped != "Unknown":
            return mapped

        match = re.fullmatch(r"\d+", text)
        if match:
            return f"Quận {text}"
        return title_case_vietnamese(text).replace("Q.", "Quận").replace("P.", "Phường")

    if entity == "ward":
        mapped = map_alias(text, WARD_ALIASES)
        if mapped != "Unknown":
            return mapped

        match = re.fullmatch(r"\d+", text)
        if match:
            return f"Phường {text}"
        return title_case_vietnamese(text).replace("Q.", "Quận").replace("P.", "Phường")

    return title_case_vietnamese(text)


def parse_location_fields(address):
    if pd.isna(address):
        return {"city": "Unknown", "district": "Unknown", "ward": "Unknown", "area": "Unknown"}

    text = str(address).strip()
    if not text:
        return {"city": "Unknown", "district": "Unknown", "ward": "Unknown", "area": "Unknown"}

    lower = text.lower()
    city = "Unknown"
    district = "Unknown"
    ward = "Unknown"

    if any(keyword in lower for keyword in ["ho chi minh", "hồ chí minh", "thành phố hồ chí minh", "tp.hcm", "tp hcm", "hcm", "ho chi minh city", "ho chi minh city,", "thành phố hcm"]):
        city = "Hồ Chí Minh"

    district_candidates = re.findall(
        r"(?:quận|quan|district|dist|q\.?|huyện|huyen|h\.)\s*([0-9a-zà-ỹ\s.-]+?)(?=(?:,|;|\||$))",
        text,
        flags=re.IGNORECASE,
    )
    for candidate in district_candidates:
        cleaned = re.sub(r"\s+", " ", candidate).strip(" .-")
        if cleaned:
            district = normalize_place_label(cleaned, "district")
            break

    ward_candidates = re.findall(
        r"(?:phường|phuong|ward|w\.?|xã|xa|thị trấn|tt\.?|p\.?|x\.)\s*([0-9a-zà-ỹ\s.-]+?)(?=(?:,|;|\||$))",
        text,
        flags=re.IGNORECASE,
    )
    for candidate in ward_candidates:
        cleaned = re.sub(r"\s+", " ", candidate).strip(" .-")
        if cleaned:
            ward = normalize_place_label(cleaned, "ward")
            break

    if district == "Unknown" and ward != "Unknown":
        area = ward
    elif district != "Unknown":
        area = district
    elif city != "Unknown":
        area = city
    else:
        area = "Chưa xác định"

    return {
        "city": city,
        "district": district,
        "ward": ward,
        "area": area,
    }


def enrich_poi_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["category_normalized"] = out["category"].apply(normalize_category)

    location_data = out["address"].apply(parse_location_fields)
    location_df = pd.DataFrame(list(location_data))
    out = pd.concat([out.reset_index(drop=True), location_df.reset_index(drop=True)], axis=1)

    if "area" not in out.columns:
        out["area"] = "Unknown"

    out["area"] = out["area"].fillna("Unknown").astype(str)
    out["district"] = out["district"].fillna("Unknown").astype(str)
    out["ward"] = out["ward"].fillna("Unknown").astype(str)
    out["city"] = out["city"].fillna("Unknown").astype(str)

    out["district"] = out["district"].replace({"": "Unknown"})
    out["ward"] = out["ward"].replace({"": "Unknown"})
    out["area"] = out["area"].replace({"": "Unknown"})

    if out["area"].eq("Unknown").all():
        out["area"] = out["district"].where(out["district"] != "Unknown", out["ward"])
        out["area"] = out["area"].replace("Unknown", "Chưa xác định")

    out["area"] = out["area"].replace({"Unknown": "Chưa xác định"})
    out["district"] = out["district"].replace({"Unknown": "Chưa xác định"})
    out["ward"] = out["ward"].replace({"Unknown": "Chưa xác định"})
    out["city"] = out["city"].replace({"Unknown": "Chưa xác định"})

    return out


def infer_area_column(df: pd.DataFrame) -> str:
    candidates = [
        "district",
        "ward",
        "city",
        "area",
        "addr:district",
        "addr:subdistrict",
        "addr:city",
        "region",
    ]
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return "area"


def build_area_field(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "area" in out.columns:
        out["area"] = out["area"].fillna("Unknown").astype(str)
    else:
        area_col = infer_area_column(out)
        out["area"] = out[area_col].fillna("Unknown").astype(str)

    out["area"] = out["area"].replace({"": "Unknown"})
    return out


def compute_summary(df: pd.DataFrame):
    out = df.copy()
    out = build_area_field(out)

    category_counts = (
        out["category_normalized"].fillna("unknown").astype(str).value_counts().reset_index()
    )
    category_counts.columns = ["category", "count"]

    area_counts = out.groupby("area", dropna=False)["osm_id"].count().reset_index(name="count")

    missing_columns = [
        ("missing_name", "name"),
        ("missing_address", "address"),
        ("missing_phone", "phone"),
        ("missing_website", "website"),
        ("missing_hours", "opening_hours"),
    ]

    missing_summary = []
    for metric_name, col in missing_columns:
        total = len(out)
        missing_count = out[col].fillna("").astype(str).str.strip().eq("").sum()
        missing_summary.append({"metric": metric_name, "missing_count": int(missing_count), "missing_pct": round((missing_count / total) * 100, 2) if total else 0.0})

    summary = {
        "total_pois": len(out),
        "unique_categories": out["category_normalized"].nunique(dropna=False),
        "unique_areas": out["area"].nunique(dropna=False),
        "top_category": category_counts.iloc[0]["category"] if not category_counts.empty else "unknown",
        "top_category_count": int(category_counts.iloc[0]["count"]) if not category_counts.empty else 0,
        "quality_avg": round(float(out.get("quality_score", 100).fillna(100).mean()), 2) if "quality_score" in out.columns else 0.0,
    }

    return {
        "summary": summary,
        "category_counts": category_counts,
        "area_counts": area_counts,
        "missing_summary": pd.DataFrame(missing_summary),
    }


def main():
    if not DEFAULT_INPUT.exists():
        raise FileNotFoundError(f"Input file not found: {DEFAULT_INPUT}. Run dedupe_poi.py first.")

    df = pd.read_parquet(DEFAULT_INPUT)
    enriched_df = enrich_poi_data(df)
    enriched_df.to_parquet(ENRICHED_OUTPUT, index=False)

    result = compute_summary(enriched_df)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result["summary"]]).to_csv(SUMMARY_PATH, index=False)

    category_by_area = (
        enriched_df.groupby(["area", "category_normalized"], dropna=False)["osm_id"].count().reset_index(name="count")
    )
    category_by_area.to_csv(GROUP_PATH, index=False)

    print("POI enrichment completed:")
    print(f"- enriched records: {len(enriched_df):,}")
    print(f"- unique categories: {enriched_df['category_normalized'].nunique(dropna=False)}")
    print(f"- unique areas: {enriched_df['area'].nunique(dropna=False)}")
    print(f"- saved enriched file: {ENRICHED_OUTPUT}")

    print("\nTop categories:")
    print(result["category_counts"].head(10).to_string(index=False))

    print("\nArea summary:")
    print(result["area_counts"].head(10).to_string(index=False))

    print("\nMissing summary:")
    print(result["missing_summary"].to_string(index=False))

    print(f"\nSaved summary to: {SUMMARY_PATH}")
    print(f"Saved category-by-area to: {GROUP_PATH}")


if __name__ == "__main__":
    main()
