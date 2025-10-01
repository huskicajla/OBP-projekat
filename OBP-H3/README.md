# OBP CRUD Benchmark (H3 – dodatne opcije)

Ovaj projekat je proširena verzija testiranja performansi CRUD operacija (**INSERT, SELECT, UPDATE, DELETE**) nad bazom podataka **StackOverflow2013**. Za razliku od osnovnog dijela (2-tier i 3-tier poređenje), ovdje su dodane dodatne opcije i scenariji testiranja koji uključuju **connection pooling** i različite načine parametarizacije upita. Cilj je dublje analizirati kako indeksiranje, pooling i način izvršavanja SQL-a utiču na performanse.

Struktura projekta sadrži fajlove:  
- `api_main_h3.py` predstavlja FastAPI server sa podrškom za connection pooling (koristi Python `queue.Queue` za upravljanje konekcijama) i opciju uključivanja/isključivanja parametarizovanih upita.  
- `client_bench_h3.py` je klijent koji poziva 3-tier API i bilježi performanse CRUD operacija, s dodatnim opcijama `--pool` i `--param` za kontrolu rada API-ja. Rezultati se snimaju u CSV fajl `results_3tier_h3.csv`.  
- `runner_h3.py` omogućava pokretanje testova u 2-tier arhitekturi sa istim parametrima (pooling, parametri) i snima rezultate u `results_2tier_h3.csv`.  
- `load3.py` služi za testiranje konkurentnog izvršavanja SELECT upita sa više niti, te snima latenciju (p50 i p95 vrijednosti) u CSV fajl `results_3tier_concurrency.csv`.  
- `db.py` sadrži funkciju `get_conn` za kreiranje konekcije na SQL Server koristeći ODBC, sa konfiguracijom učitanom iz `.env` fajla.  
- `sqltexts.py` definiše sve SQL naredbe koje se koriste u testovima (kreiranje pomoćne tabele, indeksiranje, insert, select, update, delete).  
- `test_conn.py` je jednostavan test skript za provjeru konekcije sa bazom.  

Pored ovoga, postoje i fajlovi `.env` (koji sadrži podešavanja baze) te `requirements-2tier.txt` i `requirements-3tier.txt` za Python zavisnosti.  

Za instalaciju je potrebno klonirati projekat, kreirati virtualno okruženje, instalirati zavisnosti iz odgovarajućeg requirements fajla i podesiti `.env` konfiguraciju. Primjer `.env` fajla:  

DB_SERVER=DESKTOP-3ENDG3G\MSSQLSERVER01
DB_NAME=StackOverflow2013
DB_AUTH=windows

Ako se koristi SQL autentifikacija, mogu se dodati i varijable `DB_USER` i `DB_PASSWORD`.  

Pokretanje testova može se raditi na više načina. Za 2-tier pristup koristi se `runner_h3.py`, npr:  
python -m app.runner_h3 --iters 3 --n 100 --with-index --pool on --param on

što pokreće set CRUD testova tri puta, sa ubacivanjem 100 redova, aktivnim indeksom, uključenim connection poolingom i parametrizacijom upita. Rezultati se čuvaju u `reports/results_2tier_h3.csv`.  

Za 3-tier arhitekturu prvo se pokreće FastAPI server:  
uvicorn app.api_main_h3:app --reload

a zatim klijent:  
python -m app.client_bench_h3 --iters 3 --n 100 --with-index --pool on --param on

Rezultati se čuvaju u `reports/results_3tier_h3.csv`.  

Za testiranje konkurentnosti može se koristiti:  
python -m app.load3 --threads 10 --rounds 5 --with-index --pool on --param on

što će pokrenuti 10 niti, svaka sa 5 SELECT upita, i rezultati će biti snimljeni u `results_3tier_concurrency.csv` uključujući median (p50) i p95 latenciju.  

Parametri dostupni u svim skriptama uključuju:  
- `--iters` broj ponavljanja CRUD ciklusa (default 3)  
- `--n` broj redova za INSERT (default 100)  
- `--sel-top` broj redova u SELECT upitu (default 200)  
- `--from`, `--to` vremenski interval za SELECT upit  
- `--update-k` broj redova koji se ažurira u UPDATE  
- `--with-index` uključuje ili isključuje indeks nad `Posts.CreationDate`  
- `--pool` određuje da li se koristi connection pooling (`on` ili `off`)  
- `--param` određuje da li se koriste parametarizovani upiti (`on` ili `off`)  

Rezultati testova se bilježe u CSV fajlove unutar foldera `reports/` i sadrže informacije o arhitekturi (`2-tier` ili `3-tier`), da li je korišten indeks, status poolinga i parametara, vrstu CRUD operacije, vrijeme izvođenja (`elapsed_ms`), broj obrađenih redova (`rows`) te kod konkurentnog testiranja dodatno p50 i p95 latenciju.  

Projekt koristi Python 3.10+, FastAPI, Uvicorn, pyodbc, pandas i requests. Za rad je neophodan instaliran SQL Server sa bazom **StackOverflow2013** i odgovarajućim ODBC drajverom (npr. *ODBC Driver 17 for SQL Server*).  
