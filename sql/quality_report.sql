-- Quality reports using the columns available in schema_postgresql.sql.
-- Latest assessment per POI is used if the table contains multiple assessments.

WITH latest_quality AS (
    SELECT DISTINCT ON (q.poi_id)
        q.quality_id,
        q.poi_id,
        q.quality_score,
        q.quality_status,
        q.duplicate_flag,
        q.assessed_at
    FROM public.poi_quality AS q
    ORDER BY q.poi_id, q.assessed_at DESC, q.quality_id DESC
)
SELECT
    (SELECT COUNT(*) FROM public.poi) AS total_pois,
    COUNT(q.poi_id) AS assessed_pois,
    ROUND(AVG(q.quality_score), 2) AS average_quality_score,
    COUNT(*) FILTER (WHERE q.quality_status IN ('GOOD', 'EXCELLENT')) AS good_pois,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE q.quality_status IN ('GOOD', 'EXCELLENT'))
        / NULLIF(COUNT(q.poi_id), 0),
        2
    ) AS quality_rate_pct,
    COUNT(*) FILTER (WHERE q.quality_status = 'WARNING') AS warning_pois,
    COUNT(*) FILTER (WHERE q.quality_status = 'POOR') AS poor_pois,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(p.name), '') IS NULL
           OR LOWER(BTRIM(p.name)) = 'unknown'
    ) AS missing_name_count,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(p.address), '') IS NULL
           OR LOWER(BTRIM(p.address)) IN ('unknown', 'chưa xác định')
    ) AS missing_address_count,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(p.phone), '') IS NULL
    ) AS missing_phone_count,
    COUNT(*) FILTER (
        WHERE p.latitude IS NULL
           OR p.latitude NOT BETWEEN -90 AND 90
           OR p.longitude IS NULL
           OR p.longitude NOT BETWEEN -180 AND 180
    ) AS invalid_coordinate_count,
    COUNT(*) FILTER (WHERE q.duplicate_flag IS TRUE) AS duplicate_flag_count
FROM public.poi AS p
LEFT JOIN latest_quality AS q ON q.poi_id = p.poi_id;

-- Latest quality by category. The schema stores category on poi, not category_normalized.
WITH latest_quality AS (
    SELECT DISTINCT ON (q.poi_id)
        q.poi_id,
        q.quality_score,
        q.quality_status,
        q.duplicate_flag
    FROM public.poi_quality AS q
    ORDER BY q.poi_id, q.assessed_at DESC, q.quality_id DESC
)
SELECT
    COALESCE(NULLIF(BTRIM(p.category), ''), 'unknown') AS category,
    COUNT(*) AS total_pois,
    ROUND(AVG(q.quality_score), 2) AS average_quality_score,
    COUNT(*) FILTER (WHERE q.quality_status IN ('GOOD', 'EXCELLENT')) AS good_pois,
    COUNT(*) FILTER (WHERE q.quality_status = 'WARNING') AS warning_pois,
    COUNT(*) FILTER (WHERE q.quality_status = 'POOR') AS poor_pois,
    COUNT(*) FILTER (WHERE q.duplicate_flag IS TRUE) AS duplicate_flag_count
FROM public.poi AS p
JOIN latest_quality AS q ON q.poi_id = p.poi_id
GROUP BY COALESCE(NULLIF(BTRIM(p.category), ''), 'unknown')
ORDER BY total_pois DESC;

-- Missing fields available in poi. Website/opening-hours are not in this schema.
SELECT
    COUNT(*) AS total_pois,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(name), '') IS NULL OR LOWER(BTRIM(name)) = 'unknown'
    ) AS missing_name_count,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE NULLIF(BTRIM(name), '') IS NULL OR LOWER(BTRIM(name)) = 'unknown'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS missing_name_pct,
    COUNT(*) FILTER (
        WHERE NULLIF(BTRIM(address), '') IS NULL
           OR LOWER(BTRIM(address)) IN ('unknown', 'chưa xác định')
    ) AS missing_address_count,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE NULLIF(BTRIM(address), '') IS NULL
               OR LOWER(BTRIM(address)) IN ('unknown', 'chưa xác định')
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS missing_address_pct,
    COUNT(*) FILTER (WHERE NULLIF(BTRIM(phone), '') IS NULL) AS missing_phone_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE NULLIF(BTRIM(phone), '') IS NULL)
        / NULLIF(COUNT(*), 0),
        2
    ) AS missing_phone_pct
FROM public.poi;

-- Issues by issue type/category using existing issue fields.
SELECT
    i.issue_type,
    COALESCE(NULLIF(BTRIM(p.category), ''), 'unknown') AS category,
    i.severity,
    i.priority,
    i.status,
    COUNT(DISTINCT i.issue_id) AS issue_count,
    COUNT(DISTINCT i.poi_id) AS affected_poi_count
FROM public.poi_issue AS i
JOIN public.poi AS p ON p.poi_id = i.poi_id
GROUP BY i.issue_type, COALESCE(NULLIF(BTRIM(p.category), ''), 'unknown'),
         i.severity, i.priority, i.status
ORDER BY issue_count DESC;

-- Duplicate candidates are sourced from the candidate table, not quality flags.
SELECT
    status,
    match_type,
    COUNT(*) AS candidate_count,
    ROUND(AVG(similarity_score), 2) AS average_similarity_score
FROM public.poi_duplicate_candidate
GROUP BY status, match_type
ORDER BY candidate_count DESC;
