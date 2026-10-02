import geopandas as gpd
import pandas as pd
import re
import json


INPUT_FILE = "data/raw/hcmc.osm.gpkg"
OUTPUT_FILE = "data/processed/hcmc_poi.parquet"


# --------------------------------------------------
# 1. Load OSM points
# --------------------------------------------------

print("Loading OSM points...")

gdf = gpd.read_file(
    INPUT_FILE,
    layer="points"
)

print(f"Total point records: {len(gdf):,}")


# --------------------------------------------------
# 2. Parse OSM other_tags
# --------------------------------------------------

def parse_other_tags(value):

    if pd.isna(value):
        return {}

    result = {}

    # OSM GeoPackage format:
    # "key"=>"value","key2"=>"value2"

    matches = re.findall(
        r'"([^"]+)"=>"([^"]*)"',
        str(value)
    )

    for key, val in matches:
        result[key] = val

    return result


print("Parsing OSM tags...")

tags = gdf["other_tags"].apply(parse_other_tags)

tags_df = pd.json_normalize(tags)

gdf = pd.concat(
    [
        gdf.reset_index(drop=True),
        tags_df.reset_index(drop=True)
    ],
    axis=1
)


# --------------------------------------------------
# 3. Identify POIs
# --------------------------------------------------

poi_columns = [
    "amenity",
    "shop",
    "tourism",
    "office",
    "leisure",
    "healthcare",
    "craft",
    "emergency"
]

existing_columns = [
    col for col in poi_columns
    if col in gdf.columns
]

print("\nAvailable POI tags:")
print(existing_columns)


# Keep records having at least one POI category
poi_mask = gdf[existing_columns].notna().any(axis=1)

poi = gdf[poi_mask].copy()

print(
    f"\nPOI candidates: {len(poi):,}"
)


# --------------------------------------------------
# 4. Create unified category
# --------------------------------------------------

def get_category(row):

    for col in existing_columns:

        value = row.get(col)

        if pd.notna(value) and str(value).strip():

            return str(value).strip()

    return None


poi["category"] = poi.apply(
    get_category,
    axis=1
)


# --------------------------------------------------
# 5. Standardize name
# --------------------------------------------------

poi["name"] = (
    poi["name"]
    .astype("string")
    .str.strip()
)


# Prefer Vietnamese name
if "name:vi" in poi.columns:

    poi["name_vi"] = (
        poi["name:vi"]
        .astype("string")
        .str.strip()
    )

else:

    poi["name_vi"] = pd.NA


# Prefer English name
if "name:en" in poi.columns:

    poi["name_en"] = (
        poi["name:en"]
        .astype("string")
        .str.strip()
    )

else:

    poi["name_en"] = pd.NA


# --------------------------------------------------
# 6. Address fields
# --------------------------------------------------

address_fields = [
    "addr:housenumber",
    "addr:street",
    "addr:place",
    "addr:district",
    "addr:subdistrict",
    "addr:province",
    "addr:city",
    "addr:postcode"
]

for col in address_fields:

    if col not in poi.columns:
        poi[col] = pd.NA


def build_address(row):

    parts = []

    for col in address_fields:

        value = row.get(col)

        if pd.notna(value):

            value = str(value).strip()

            if value:
                parts.append(value)

    if not parts:
        return pd.NA

    return ", ".join(parts)


poi["address"] = poi.apply(
    build_address,
    axis=1
)


# --------------------------------------------------
# 7. Coordinates
# --------------------------------------------------

poi["longitude"] = poi.geometry.x
poi["latitude"] = poi.geometry.y


# --------------------------------------------------
# 8. Phone / website / opening hours
# --------------------------------------------------

for col in [
    "phone",
    "website",
    "opening_hours",
    "brand",
    "cuisine",
    "operator"
]:

    if col not in poi.columns:
        poi[col] = pd.NA


# --------------------------------------------------
# 9. OSM ID
# --------------------------------------------------

poi["osm_id"] = poi["osm_id"].astype("Int64")


# --------------------------------------------------
# 10. Select final columns
# --------------------------------------------------

final_columns = [
    "osm_id",
    "name",
    "name_vi",
    "name_en",
    "category",
    "address",
    "phone",
    "website",
    "opening_hours",
    "brand",
    "cuisine",
    "operator",
    "latitude",
    "longitude",
    "geometry"
]

poi = poi[final_columns]


# --------------------------------------------------
# 11. Remove duplicate OSM IDs
# --------------------------------------------------

before = len(poi)

poi = poi.drop_duplicates(
    subset=["osm_id"]
)

after = len(poi)

print(
    f"Removed duplicate OSM IDs: {before - after:,}"
)


# --------------------------------------------------
# 12. Save
# --------------------------------------------------

poi.to_parquet(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nSaved {len(poi):,} POIs to:"
)

print(OUTPUT_FILE)


# --------------------------------------------------
# 13. Basic report
# --------------------------------------------------

print("\nPOI by category:")

print(
    poi["category"]
    .value_counts()
    .head(30)
)


print("\nMissing values:")

print(
    poi[
        [
            "name",
            "category",
            "address",
            "phone",
            "latitude",
            "longitude"
        ]
    ]
    .isna()
    .sum()
)