-- Operations dashboard queries for the current POI issue/task data.
-- Current exports contain OPEN issues, NEW tasks, one data_quality team,
-- and NULL resolved_at values. These queries report the stored values as-is.

-- KPI cards: use active/open and data-coverage metrics supported by the schema.
WITH poi_totals AS (
    SELECT COUNT(*) AS total_pois
    FROM public.poi
), issue_totals AS (
    SELECT
        COUNT(*) AS total_issues,
        COUNT(*) FILTER (WHERE i.status = 'OPEN') AS open_issues,
        COUNT(*) FILTER (WHERE i.status = 'IN_PROGRESS') AS in_progress_issues,
        COUNT(*) FILTER (WHERE i.status IN ('RESOLVED', 'CLOSED')) AS resolved_issues,
        COUNT(*) FILTER (WHERE i.severity = 'CRITICAL') AS critical_issues,
        COUNT(*) FILTER (WHERE i.severity = 'HIGH') AS high_severity_issues,
        COUNT(*) FILTER (WHERE i.severity = 'MEDIUM') AS medium_severity_issues,
        COUNT(*) FILTER (WHERE i.priority = 'HIGH') AS high_priority_issues,
        COUNT(DISTINCT i.poi_id) AS affected_pois,
        COUNT(*) FILTER (WHERE i.resolved_at IS NOT NULL) AS issues_with_resolution_time,
        ROUND(AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.detected_at)) / 3600)
            FILTER (WHERE i.resolved_at IS NOT NULL), 2) AS average_resolution_hours
    FROM public.poi_issue AS i
), task_totals AS (
    SELECT
        COUNT(*) AS total_tasks,
        COUNT(*) FILTER (WHERE t.status = 'NEW') AS new_tasks,
        COUNT(*) FILTER (WHERE t.status = 'IN_PROGRESS') AS in_progress_tasks,
        COUNT(*) FILTER (WHERE t.status = 'DONE') AS done_tasks,
        COUNT(DISTINCT t.assigned_team) AS assigned_team_count
    FROM public.operation_task AS t
)
SELECT
    p.total_pois,
    i.total_issues,
    i.open_issues,
    i.in_progress_issues,
    i.resolved_issues,
    i.critical_issues,
    i.high_severity_issues,
    i.medium_severity_issues,
    i.high_priority_issues,
    i.affected_pois,
    ROUND(100.0 * i.affected_pois / NULLIF(p.total_pois, 0), 2) AS issue_coverage_pct,
    t.total_tasks,
    t.new_tasks,
    t.in_progress_tasks,
    t.done_tasks,
    t.assigned_team_count,
    i.issues_with_resolution_time,
    i.average_resolution_hours
FROM poi_totals AS p
CROSS JOIN issue_totals AS i
CROSS JOIN task_totals AS t;

-- Open issues by issue type, severity, and priority.
SELECT
    i.issue_type,
    i.severity,
    i.priority,
    i.status,
    COUNT(*) AS issue_count,
    COUNT(DISTINCT i.poi_id) AS affected_poi_count
FROM public.poi_issue AS i
GROUP BY i.issue_type, i.severity, i.priority, i.status
ORDER BY issue_count DESC, i.issue_type;

-- Tasks by assigned team and task status. Priority belongs to poi_issue, not operation_task.
SELECT
    COALESCE(NULLIF(BTRIM(t.assigned_team), ''), 'unassigned') AS assigned_team,
    t.status AS task_status,
    COUNT(DISTINCT t.task_id) AS task_count,
    COUNT(DISTINCT i.issue_id) AS linked_issue_count,
    COUNT(DISTINCT i.issue_id) FILTER (WHERE i.priority = 'HIGH') AS high_priority_issue_count
FROM public.operation_task AS t
JOIN public.poi_issue AS i ON i.issue_id = t.issue_id
GROUP BY COALESCE(NULLIF(BTRIM(t.assigned_team), ''), 'unassigned'), t.status
ORDER BY task_count DESC, assigned_team, task_status;

-- Issue detections by date. This is not status history; current data has no status events.
SELECT
    i.detected_at::date AS detected_date,
    i.status,
    COUNT(*) AS issue_count
FROM public.poi_issue AS i
GROUP BY i.detected_at::date, i.status
ORDER BY detected_date, i.status;

-- Current issue queue. NULL resolved_at means the issue has not been resolved.
SELECT
    i.issue_id,
    i.poi_id,
    p.name AS poi_name,
    p.category,
    i.issue_type,
    i.severity,
    i.priority,
    i.status AS issue_status,
    COALESCE(NULLIF(BTRIM(t.assigned_team), ''), 'unassigned') AS assigned_team,
    t.status AS task_status,
    i.detected_at,
    i.resolved_at,
    ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - i.detected_at)) / 3600, 2) AS open_age_hours
FROM public.poi_issue AS i
JOIN public.poi AS p ON p.poi_id = i.poi_id
LEFT JOIN public.operation_task AS t ON t.issue_id = i.issue_id
WHERE i.status = 'OPEN'
ORDER BY
    CASE i.priority
        WHEN 'URGENT' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END,
    i.detected_at ASC,
    i.issue_id
LIMIT 500;
