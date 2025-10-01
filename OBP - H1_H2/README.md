# OBP CRUD Benchmark (2-tier vs 3-tier)

Ovaj projekat implementira testiranje performansi CRUD operacija (**INSERT, SELECT, UPDATE, DELETE**) nad bazom podataka **StackOverflow2013** u dvije različite arhitekture:  
- **2-tier** → aplikacija direktno komunicira sa bazom (`runner.py`)  
- **3-tier** → korištenjem REST API sloja preko **FastAPI** (`api_main.py` + `client_bench.py`)  

Cilj je analizirati utjecaj **indeksiranja** na performanse i porediti rezultate između arhitektura.  


## 📂 Struktura projekta

app/
├── api_main.py # FastAPI server za 3-tier arhitekturu
├── client_bench.py # Klijent koji poziva 3-tier API i mjeri performanse
├── runner.py # 2-tier skripta za direktno testiranje CRUD-a
├── db.py # Konekcija na SQL Server bazu (pyodbc + .env)
├── sqltexts.py # SQL skripte za CRUD operacije i indeksiranje
└── __init__.py # prazan fajl

.env # Konfiguracija baze (server, auth, ime baze)
requirements-3tier.txt # Potrebne Python biblioteke
requirements2.txt # (prazan, rezervisan za 2-tier zavisnosti)
reports/ # CSV fajlovi sa rezultatima (automatski se kreiraju)

## ⚙️ Instalacija

1. Klonirati repozitorij i ući u folder projekta.  
2. Kreirati virtualno okruženje (preporučeno):  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
Instalirati zavisnosti:

pip install -r requirements-3tier.txt
Podesiti .env fajl (primjer):

DB_SERVER=DESKTOP-3ENDG3G\MSSQLSERVER01
DB_NAME=StackOverflow2013
DB_AUTH=windows
Ako se koristi SQL autentifikacija:

DB_AUTH=sql
DB_USER=sa
DB_PASSWORD=lozinka123
▶️ Pokretanje
🔹 2-tier arhitektura
Pokrenuti CRUD testove direktno na bazi:

python -m app.runner --iters 3 --n 100 --with-index
Rezultati se snimaju u: reports/results_raw.csv

🔹 3-tier arhitektura
Pokrenuti API server:

uvicorn app.api_main:app --reload
U drugom terminalu pokrenuti klijenta:

python -m app.client_bench --iters 3 --n 100 --with-index
Rezultati se snimaju u: reports/results_3tier_raw.csv

⚙️ Parametri
--iters → broj ponavljanja CRUD seta (default: 3)

--n → broj redova za INSERT (default: 100)

--sel-top → broj redova u SELECT (default: 200)

--from, --to → vremenski period u SELECT upitu

--update-k → broj redova koje mijenja UPDATE

--with-index → koristi indeks nad Posts.CreationDate

📊 Rezultati
CSV fajlovi sadrže mjerene vrijednosti:

arch → arhitektura (2-tier ili 3-tier)

with_index → da li je indeks korišten

crud → tip operacije (INSERT, SELECT, UPDATE, DELETE)

elapsed_ms → vrijeme izvođenja u milisekundama

rows → broj obrađenih redova

🛠️ Tehnologije
Python 3.10+

FastAPI + Uvicorn

pyodbc (SQL Server ODBC konekcija)

requests (za API pozive)

pandas (za analizu rezultata)

📌 Napomena
Potrebno je imati instaliran SQL Server i bazu StackOverflow2013.

ODBC driver mora biti instaliran (npr. ODBC Driver 17 for SQL Server).