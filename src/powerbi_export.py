from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "processed" / "hcmc_poi_enriched.parquet"
POWERBI_DATASET = ROOT / "data" / "processed" / "powerbi_poi_dataset.csv"
AREA_SUMMARY = ROOT / "data" / "processed" / "powerbi_area_summary.csv"
DASHBOARD_HTML = ROOT / "dashboard" / "powerbi_mockup.html"
DB_POI_EXPORT = ROOT / "data" / "processed" / "db_poi.csv"
DB_POI_QUALITY_EXPORT = ROOT / "data" / "processed" / "db_poi_quality.csv"
DB_POI_ISSUE_EXPORT = ROOT / "data" / "processed" / "db_poi_issue.csv"
DB_OPERATION_TASK_EXPORT = ROOT / "data" / "processed" / "db_operation_task.csv"
DB_POI_DUPLICATE_EXPORT = ROOT / "data" / "processed" / "db_poi_duplicate_candidate.csv"


def build_bi_dataset(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [
        "osm_id",
        "name",
        "category",
        "category_normalized",
        "address",
        "city",
        "district",
        "ward",
        "area",
        "phone",
        "website",
        "opening_hours",
        "brand",
        "cuisine",
        "operator",
        "latitude",
        "longitude",
        "quality_score",
        "issue_count",
        "name_missing",
        "address_missing",
        "category_missing",
        "phone_missing",
        "website_missing",
        "hours_missing",
        "invalid_geo",
    ]

    out = df.copy()
    for col in keep_cols:
        if col not in out.columns:
            out[col] = None

    out = out[keep_cols].copy()
    out["category"] = out["category_normalized"].fillna(out["category"]).fillna("unknown")
    out["name"] = out["name"].fillna("Unknown")
    out["address"] = out["address"].fillna("Chưa xác định")
    out["city"] = out["city"].fillna("Chưa xác định")
    out["district"] = out["district"].fillna("Chưa xác định")
    out["ward"] = out["ward"].fillna("Chưa xác định")
    out["area"] = out["area"].fillna("Chưa xác định")

    if "quality_score" in out.columns:
        out["quality_score"] = pd.to_numeric(out["quality_score"], errors="coerce").fillna(0)

    return out


def build_area_summary(df: pd.DataFrame) -> pd.DataFrame:
    area_summary = (
        df.groupby(["area", "category"], dropna=False)["osm_id"]
        .count()
        .reset_index(name="poi_count")
        .sort_values(["area", "poi_count"], ascending=[True, False])
    )
    return area_summary


def render_dashboard_mockup(df: pd.DataFrame, summary_df: pd.DataFrame):
    top_categories = (
        df["category"].fillna("unknown").astype(str).value_counts().head(8).reset_index()
    )
    top_categories.columns = ["category", "count"]

    total_pois = len(df)
    unique_categories = df["category"].nunique(dropna=False)
    avg_quality = round(float(df["quality_score"].fillna(0).mean()), 2) if "quality_score" in df.columns else 0
    top_category = top_categories.iloc[0]["category"] if not top_categories.empty else "unknown"

    max_count = max(top_categories["count"].max(), 1)
    bars = []
    for _, row in top_categories.iterrows():
        ratio = round((row["count"] / max_count) * 100)
        bars.append(
            f"<div class='bar-row'><span>{row['category']}</span><div class='bar'><i style='width:{ratio}%'></i></div><b>{int(row['count'])}</b></div>"
        )

    area_rows = []
    for _, row in summary_df.head(8).iterrows():
        area_rows.append(
            f"<tr><td>{row['area']}</td><td>{row['poi_count']}</td><td>{row['category']}</td></tr>"
        )

    html = f"""
    <!doctype html>
    <html lang='en'>
    <head>
        <meta charset='utf-8' />
        <title>POI Operations Dashboard Mockup</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f3f6fb; margin: 0; padding: 24px; color: #122033; }}
            .wrap {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ margin-bottom: 12px; }}
            .subtitle {{ color: #4b5d75; margin-bottom: 24px; }}
            .cards {{ display: grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
            .card {{ background: white; border-radius: 14px; box-shadow: 0 4px 16px rgba(18,32,51,0.06); padding: 18px; }}
            .label {{ font-size: 12px; text-transform: uppercase; color: #6b7a90; letter-spacing: 0.06em; }}
            .value {{ font-size: 30px; font-weight: bold; margin-top: 8px; }}
            .panel {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 18px rgba(18,32,51,0.05); }}
            .grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; }}
            .bar-chart {{ margin-top: 10px; }}
            .bar-row {{ display: grid; grid-template-columns: 140px 1fr 50px; gap: 12px; align-items: center; margin-bottom: 10px; font-size: 14px; }}
            .bar {{ height: 12px; background: #edf2ff; border-radius: 999px; overflow: hidden; }}
            .bar i {{ display: block; height: 100%; background: linear-gradient(90deg, #2f6fed, #72a2ff); border-radius: 999px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
            th, td {{ padding: 10px 12px; border-bottom: 1px solid #edf0f4; text-align: left; }}
            th {{ color: #5a6d85; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
        </style>
    </head>
    <body>
        <div class='wrap'>
            <h1>POI Operations Analytics</h1>
            <div class='subtitle'>Map Data Quality & Analytics Mockup</div>

            <div class='cards'>
                <div class='card'>
                    <div class='label'>Total POIs</div>
                    <div class='value'>{total_pois:,}</div>
                </div>
                <div class='card'>
                    <div class='label'>Categories</div>
                    <div class='value'>{unique_categories}</div>
                </div>
                <div class='card'>
                    <div class='label'>Avg Quality</div>
                    <div class='value'>{avg_quality}</div>
                </div>
                <div class='card'>
                    <div class='label'>Top Category</div>
                    <div class='value' style='font-size:22px;'>{top_category}</div>
                </div>
            </div>

            <div class='grid'>
                <div class='panel'>
                    <h3>Top categories</h3>
                    <div class='bar-chart'>
                        {''.join(bars)}
                    </div>
                </div>
                <div class='panel'>
                    <h3>Top areas</h3>
                    <table>
                        <thead>
                            <tr><th>Area</th><th>POIs</th><th>Top category</th></tr>
                        </thead>
                        <tbody>
                            {''.join(area_rows)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    DASHBOARD_HTML.write_text(html, encoding="utf-8")


def quality_status(score: float) -> str:
    if pd.isna(score):
        return "POOR"
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 50:
        return "WARNING"
    return "POOR"


def build_db_ready_exports(df: pd.DataFrame):
    data = df.copy()
    data["name"] = data["name"].fillna("Unknown")
    data["category"] = data["category_normalized"].fillna(data["category"]).fillna("unknown")
    data["address"] = data["address"].fillna("Chưa xác định")
    data["phone"] = data["phone"].fillna("")
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data["quality_score"] = pd.to_numeric(data["quality_score"], errors="coerce").fillna(0)

    now = pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    poi_rows = []
    quality_rows = []
    issue_rows = []
    task_rows = []

    for idx, row in data.reset_index(drop=True).iterrows():
        poi_id = idx + 1
        poi_rows.append(
            {
                "poi_id": poi_id,
                "name": str(row["name"]).strip()[:255],
                "category": str(row["category"]).strip()[:100],
                "address": str(row["address"]).strip()[:1000],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "phone": str(row["phone"]).strip()[:80],
                "source": "osm",
                "updated_at": now,
            }
        )

        quality_rows.append(
            {
                "quality_id": poi_id,
                "poi_id": poi_id,
                "quality_score": round(float(row["quality_score"]), 2),
                "quality_status": quality_status(float(row["quality_score"])),
                "duplicate_flag": False,
                "assessed_at": now,
            }
        )

        issue_type_map = {
            "name_missing": "missing_name",
            "address_missing": "missing_address",
            "category_missing": "missing_category",
            "invalid_geo": "invalid_geo",
        }

        issue_count = 0
        for flag_col, issue_type in issue_type_map.items():
            if bool(row.get(flag_col, False)):
                issue_count += 1
                severity = "HIGH" if issue_type in {"invalid_geo"} else "MEDIUM"
                priority = "HIGH" if issue_type in {"invalid_geo", "missing_address"} else "MEDIUM"
                issue_rows.append(
                    {
                        "issue_id": len(issue_rows) + 1,
                        "poi_id": poi_id,
                        "issue_type": issue_type,
                        "severity": severity,
                        "priority": priority,
                        "status": "OPEN",
                        "detected_at": now,
                        "resolved_at": None,
                    }
                )
                task_rows.append(
                    {
                        "task_id": len(task_rows) + 1,
                        "issue_id": len(issue_rows),
                        "assigned_team": "data_quality",
                        "status": "NEW",
                        "created_at": now,
                        "resolved_at": None,
                    }
                )

    poi_df = pd.DataFrame(poi_rows, columns=["poi_id", "name", "category", "address", "latitude", "longitude", "phone", "source", "updated_at"])
    quality_df = pd.DataFrame(quality_rows, columns=["quality_id", "poi_id", "quality_score", "quality_status", "duplicate_flag", "assessed_at"])
    issue_df = pd.DataFrame(issue_rows, columns=["issue_id", "poi_id", "issue_type", "severity", "priority", "status", "detected_at", "resolved_at"])
    task_df = pd.DataFrame(task_rows, columns=["task_id", "issue_id", "assigned_team", "status", "created_at", "resolved_at"])
    duplicate_df = pd.DataFrame(columns=["duplicate_id", "poi_id", "duplicate_poi_id", "match_type", "similarity_score", "status", "created_at", "reviewed_at"])

    return poi_df, quality_df, issue_df, task_df, duplicate_df


def main():
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Source parquet not found: {SOURCE_PATH}. Run analytics_poi.py first.")

    df = pd.read_parquet(SOURCE_PATH)

    dataset_df = build_bi_dataset(df)
    dataset_df.to_csv(POWERBI_DATASET, index=False)

    area_summary = build_area_summary(dataset_df)
    area_summary.to_csv(AREA_SUMMARY, index=False)
    render_dashboard_mockup(dataset_df, area_summary)

    poi_df, quality_df, issue_df, task_df, duplicate_df = build_db_ready_exports(df)
    poi_df.to_csv(DB_POI_EXPORT, index=False)
    quality_df.to_csv(DB_POI_QUALITY_EXPORT, index=False)
    issue_df.to_csv(DB_POI_ISSUE_EXPORT, index=False)
    task_df.to_csv(DB_OPERATION_TASK_EXPORT, index=False)
    duplicate_df.to_csv(DB_POI_DUPLICATE_EXPORT, index=False)

    print(f"Power BI dataset exported to: {POWERBI_DATASET}")
    print(f"Area summary exported to: {AREA_SUMMARY}")
    print(f"Dashboard mockup saved to: {DASHBOARD_HTML}")
    print(f"DB-ready poi exported to: {DB_POI_EXPORT}")
    print(f"DB-ready poi_quality exported to: {DB_POI_QUALITY_EXPORT}")
    print(f"DB-ready poi_issue exported to: {DB_POI_ISSUE_EXPORT}")
    print(f"DB-ready operation_task exported to: {DB_OPERATION_TASK_EXPORT}")
    print(f"DB-ready poi_duplicate_candidate exported to: {DB_POI_DUPLICATE_EXPORT}")
    print(f"Rows: {len(dataset_df):,}")


if __name__ == "__main__":
    main()
