CREATE_BENCH_TABLE = """
IF OBJECT_ID('dbo._BenchPosts','U') IS NULL
BEGIN
    CREATE TABLE dbo._BenchPosts(
        PostId INT NOT NULL PRIMARY KEY
    );
END
"""
TRUNC_BENCH = "TRUNCATE TABLE dbo._BenchPosts;"
COUNT_BENCH = "SELECT COUNT(*) FROM dbo._BenchPosts;"

DROP_INDEX_IF_EXISTS = """
IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Posts_CreationDate' AND object_id = OBJECT_ID('dbo.Posts'))
    DROP INDEX IX_Posts_CreationDate ON dbo.Posts;
"""
CREATE_INDEX = "CREATE INDEX IX_Posts_CreationDate ON dbo.Posts(CreationDate);"

SELECT_BY_DATE = """
SELECT TOP (?) p.Id, p.CreationDate, p.Score
FROM dbo.Posts AS p
WHERE p.CreationDate BETWEEN ? AND ?
ORDER BY p.CreationDate DESC;
"""

UPDATE_ON_BENCH = """
UPDATE TOP (?) p
SET p.Score = p.Score + 1
FROM dbo.Posts AS p
JOIN dbo._BenchPosts b ON b.PostId = p.Id;
"""

DELETE_ON_BENCH = """
DELETE p
FROM dbo.Posts AS p
JOIN dbo._BenchPosts b ON b.PostId = p.Id;
"""
