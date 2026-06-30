-- Index audit (P2) — run against a representative (loaded) database.
--   psql "$DATABASE_URL" -f backend/scripts/db_index_audit.sql
--
-- With 366 indexes, the goal is to (a) drop indexes nothing uses, (b) add the
-- covering index every foreign key needs for filters/joins/cascades, and
-- (c) collapse exact-duplicate indexes. Run after real traffic/seed so
-- pg_stat_user_indexes has meaningful counts; reset stats with
-- `SELECT pg_stat_reset();` at the start of a measurement window.

\echo '== 1. Unused indexes (idx_scan = 0), excluding PK/unique =='
SELECT
    s.schemaname,
    s.relname              AS table,
    s.indexrelname         AS index,
    pg_size_pretty(pg_relation_size(s.indexrelid)) AS size,
    s.idx_scan             AS scans
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0
  AND NOT i.indisprimary
  AND NOT i.indisunique
ORDER BY pg_relation_size(s.indexrelid) DESC;

\echo '== 2. Foreign keys WITHOUT a covering index (write/cascade + join cost) =='
SELECT
    c.conrelid::regclass        AS table,
    c.conname                   AS fk_constraint,
    a.attname                   AS fk_column
FROM pg_constraint c
JOIN pg_attribute a
  ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
      SELECT 1
      FROM pg_index i
      WHERE i.indrelid = c.conrelid
        AND a.attnum = ANY (i.indkey)
        AND i.indkey[0] = a.attnum   -- column is the LEADING index column
  )
ORDER BY c.conrelid::regclass::text, c.conname;

\echo '== 3. Duplicate indexes (same table + same column set) =='
SELECT
    indrelid::regclass AS table,
    array_agg(indexrelid::regclass) AS duplicate_indexes,
    indkey              AS columns
FROM pg_index
GROUP BY indrelid, indkey
HAVING count(*) > 1;

\echo '== 4. Largest indexes (review for necessity) =='
SELECT
    s.relname AS table,
    s.indexrelname AS index,
    pg_size_pretty(pg_relation_size(s.indexrelid)) AS size,
    s.idx_scan AS scans
FROM pg_stat_user_indexes s
ORDER BY pg_relation_size(s.indexrelid) DESC
LIMIT 25;
