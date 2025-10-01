# Pomoćne SQL skripte 

CREATE_BENCH_TABLE = """
IF OBJECT_ID('dbo._BenchPosts', 'U') IS NULL
    CREATE TABLE dbo._BenchPosts (PostId INT PRIMARY KEY);
"""

TRUNC_BENCH = "TRUNCATE TABLE dbo._BenchPosts;"

DROP_INDEX_IF_EXISTS = """
IF EXISTS (SELECT 1 FROM sys.indexes
           WHERE name = 'IX_Posts_CreationDate'
             AND object_id = OBJECT_ID('dbo.Posts'))
    DROP INDEX IX_Posts_CreationDate ON dbo.Posts;
"""

CREATE_INDEX = """
CREATE NONCLUSTERED INDEX IX_Posts_CreationDate
ON dbo.Posts (CreationDate)
INCLUDE (Score);
"""

# Set-based INSERT
INSERT_SET_BASED = """
DECLARE @N INT = ?;
WITH n AS (
  SELECT TOP (@N) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
  FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
INSERT INTO dbo.Posts
      (PostTypeId, Body, CreationDate, LastActivityDate, Score, ViewCount)
OUTPUT INSERTED.Id INTO dbo._BenchPosts(PostId)
SELECT 1,
       REPLICATE(N'Q', 400),
       SYSDATETIME(),
       SYSDATETIME(),
       0,
       0
FROM n;
"""

# SELECT 
SELECT_BY_DATE = """
DECLARE @From DATETIME2 = ?;
DECLARE @To   DATETIME2 = ?;

SELECT TOP (?) p.Id, p.CreationDate, p.Score
FROM dbo.Posts AS p
WHERE p.CreationDate BETWEEN @From AND @To
ORDER BY p.CreationDate DESC
OPTION (RECOMPILE);
"""

# UPDATE nad svježe ubačenim redovima 
UPDATE_ON_BENCH = """
UPDATE p
SET p.Score = p.Score + 1
FROM dbo.Posts AS p
WHERE p.Id IN (
    SELECT TOP (?) PostId
    FROM dbo._BenchPosts
    ORDER BY PostId
);
"""

# DELETE tih svježe ubačenih redova
DELETE_ON_BENCH = """
DELETE p
FROM dbo.Posts AS p
WHERE p.Id IN (SELECT PostId FROM dbo._BenchPosts);
"""

COUNT_BENCH = "SELECT COUNT(*) FROM dbo._BenchPosts;"
