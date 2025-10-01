/* ===========================================================
   OBP Istraživanje – Hipoteza 1 (1-tier / SSMS)
   Testiranje CRUD operacija: bez indeksa → sa indeksom
   Baza: StackOverflow2013
   =========================================================== */

USE StackOverflow2013;
SET NOCOUNT ON;

/* -----------------------------------------------------------
   Parametri
   ----------------------------------------------------------- */
DECLARE @N_INSERT INT      = 100;               -- broj redova za INSERT test
DECLARE @SEL_TOP  INT      = 200;               -- broj redova u SELECT testu
DECLARE @From     DATETIME2 = '2012-01-01';     -- period za SELECT filter
DECLARE @To       DATETIME2 = '2014-01-01'; 

/* -----------------------------------------------------------
   Pomoćna tabela za praćenje ubačenih redova
   ----------------------------------------------------------- */
IF OBJECT_ID('dbo._BenchPosts', 'U') IS NULL
    CREATE TABLE dbo._BenchPosts (PostId INT PRIMARY KEY);
ELSE
    TRUNCATE TABLE dbo._BenchPosts;

/* ===========================================================
   1) BEZ INDEKSA
   =========================================================== */

/* Ako već postoji indeks na CreationDate, obriši ga */
IF EXISTS (SELECT 1 FROM sys.indexes
           WHERE name = 'IX_Posts_CreationDate'
             AND object_id = OBJECT_ID('dbo.Posts'))
    DROP INDEX IX_Posts_CreationDate ON dbo.Posts;

/* -------------------- 1.1 INSERT (BEZ INDEKSA) -------------------- */
DECLARE @i INT = 1, @t0 DATETIME2 = SYSDATETIME();

WHILE @i <= @N_INSERT
BEGIN
    INSERT INTO dbo.Posts
        (PostTypeId, Body, CreationDate, LastActivityDate, Score, ViewCount)
    OUTPUT INSERTED.Id INTO dbo._BenchPosts(PostId)
    VALUES
        (1,
         REPLICATE(N'Q', 400),
         SYSDATETIME(),
         SYSDATETIME(),
         0,
         0);
    SET @i += 1;
END;

SELECT DATEDIFF(ms, @t0, SYSDATETIME()) AS ElapsedMs_Insert_NoIndex,
       (SELECT COUNT(*) FROM dbo._BenchPosts) AS InsertedRows_NoIndex;

/* -------------------- 1.2 SELECT (BEZ INDEKSA) -------------------- */
DECLARE @t1 DATETIME2 = SYSDATETIME();

SELECT TOP (@SEL_TOP) p.Id, p.CreationDate, p.Score
FROM dbo.Posts AS p
WHERE p.CreationDate BETWEEN @From AND @To
ORDER BY p.CreationDate DESC
OPTION (RECOMPILE);

SELECT DATEDIFF(ms, @t1, SYSDATETIME()) AS ElapsedMs_Select_NoIndex;

/* -------------------- 1.3 UPDATE (BEZ INDEKSA) -------------------- */
DECLARE @t2 DATETIME2 = SYSDATETIME();

UPDATE p
SET p.Score = p.Score + 1
FROM dbo.Posts AS p
WHERE p.Id IN (SELECT TOP (CASE WHEN @N_INSERT >= 50 THEN 50 ELSE @N_INSERT END)
                      PostId FROM dbo._BenchPosts ORDER BY PostId);

SELECT DATEDIFF(ms, @t2, SYSDATETIME()) AS ElapsedMs_Update_NoIndex;

/* -------------------- 1.4 DELETE (BEZ INDEKSA) -------------------- */
DECLARE @t3 DATETIME2 = SYSDATETIME();

DELETE p
FROM dbo.Posts AS p
WHERE p.Id IN (SELECT PostId FROM dbo._BenchPosts);

SELECT DATEDIFF(ms, @t3, SYSDATETIME()) AS ElapsedMs_Delete_NoIndex;

TRUNCATE TABLE dbo._BenchPosts;

/* ===========================================================
   2) SA INDEKSOM
   =========================================================== */

/* Kreiraj indeks na CreationDate */
CREATE NONCLUSTERED INDEX IX_Posts_CreationDate
ON dbo.Posts (CreationDate)
INCLUDE (Score);

/* -------------------- 2.1 INSERT (SA INDEKSOM) -------------------- */
SET @i = 1; SET @t0 = SYSDATETIME();

WHILE @i <= @N_INSERT
BEGIN
    INSERT INTO dbo.Posts
        (PostTypeId, Body, CreationDate, LastActivityDate, Score, ViewCount)
    OUTPUT INSERTED.Id INTO dbo._BenchPosts(PostId)
    VALUES
        (1,
         REPLICATE(N'Q', 400),
         SYSDATETIME(),
         SYSDATETIME(),
         0,
         0);
    SET @i += 1;
END;

SELECT DATEDIFF(ms, @t0, SYSDATETIME()) AS ElapsedMs_Insert_WithIndex,
       (SELECT COUNT(*) FROM dbo._BenchPosts) AS InsertedRows_WithIndex;

/* -------------------- 2.2 SELECT (SA INDEKSOM) -------------------- */
SET @t1 = SYSDATETIME();

SELECT TOP (@SEL_TOP) p.Id, p.CreationDate, p.Score
FROM dbo.Posts AS p
WHERE p.CreationDate BETWEEN @From AND @To
ORDER BY p.CreationDate DESC
OPTION (RECOMPILE);

SELECT DATEDIFF(ms, @t1, SYSDATETIME()) AS ElapsedMs_Select_WithIndex;

/* -------------------- 2.3 UPDATE (SA INDEKSOM) -------------------- */
SET @t2 = SYSDATETIME();

UPDATE p
SET p.Score = p.Score + 1
FROM dbo.Posts AS p
WHERE p.Id IN (SELECT TOP (CASE WHEN @N_INSERT >= 50 THEN 50 ELSE @N_INSERT END)
                      PostId FROM dbo._BenchPosts ORDER BY PostId);

SELECT DATEDIFF(ms, @t2, SYSDATETIME()) AS ElapsedMs_Update_WithIndex;

/* -------------------- 2.4 DELETE (SA INDEKSOM) -------------------- */
SET @t3 = SYSDATETIME();

DELETE p
FROM dbo.Posts AS p
WHERE p.Id IN (SELECT PostId FROM dbo._BenchPosts);

SELECT DATEDIFF(ms, @t3, SYSDATETIME()) AS ElapsedMs_Delete_WithIndex;

TRUNCATE TABLE dbo._BenchPosts;

/* ===========================================================
   3) Vraćanje baze u prvobitno stanje
   =========================================================== */
DROP INDEX IX_Posts_CreationDate ON dbo.Posts;
