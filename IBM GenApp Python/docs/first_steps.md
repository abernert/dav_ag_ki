# First Steps – Python App

Dieser Leitfaden beschreibt, wie die Python‑Applikation lokal konfiguriert und gestartet wird.

## Voraussetzungen
- Python 3.10 oder neuer
- `pip` zugänglich (idealerweise aktuell halten: `python -m pip install --upgrade pip`)
- Optional: `venv` für eine isolierte Umgebung

## Installation
```
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Konfiguration
- Datenbank‑URL über die Umgebungsvariable `DATABASE_URL`.
  - Standard (ohne Setzen): `sqlite:///./genapp.db`
  - Beispiele:
    - SQLite im Projektordner: `export DATABASE_URL=sqlite:///./genapp.db`
    - SQLite absoluter Pfad: `export DATABASE_URL=sqlite:////abs/pfad/genapp.db`
- Weitere Konfigurationen sind aktuell nicht erforderlich. Tabellen werden automatisch erstellt.

Tipp: `cp .env.example .env` und Werte anpassen. Die App lädt `.env` nicht automatisch; für eine Shell-Session kannst du exportieren, z. B. `export $(cat .env | xargs)`.

Hinweis: Für lokale Entwicklung genügt die Standard‑SQLite‑Konfiguration.

## Starten
1. Terminal im Projektverzeichnis `cics-genapp-python-port/` öffnen (dort liegen `app/`, `scripts/`, `requirements.txt`):
   ```
   uvicorn app.main:app --reload
   ```
   - UI: <http://127.0.0.1:8000/>
   - OpenAPI/Swagger: <http://127.0.0.1:8000/docs>

2. Falls du aus einem Unterordner (z. B. `cics-genapp-python-port/app`) startest, muss der Projektpfad im `PYTHONPATH` liegen, da sonst das Paket `app` nicht gefunden wird. Beispiel:
   ```
   PYTHONPATH=$(pwd)/.. uvicorn app.main:app --reload
   ```

Optional mit Port/Host:
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Was ist enthalten?
- Kunden
  - UI: Liste/Filter/Paging, Detail, Neu, Bearbeiten, Löschen
  - API: `GET/POST /api/customers`, `GET/PUT /api/customers/{id}`, `GET/PUT /api/customers/{id}/security` (inkl. Passwort-Rotation per `?rotate=true`)
- Policen
  - UI: Liste/Filter/Paging, Detail, Neu (je Typ), Bearbeiten (Basis + Typ), Löschen
  - API: `GET /api/policies`, `GET /api/policies/detailed`, `POST /api/policies`, `PUT /api/policies/{id}`
  - Typspezifisch: `POST /api/policies/{motor|house|endowment|commercial}`, `PUT /api/policies/{motor|house|endowment|commercial}/{id}`
- Schäden (Claims)
  - UI: Liste, Neu, Bearbeiten, Löschen
  - API: `GET /api/claims`, `GET /api/claims/{id}`, `POST /api/claims`, `PUT /api/claims/{id}`
- Events / Audit-Log
  - UI: Liste mit Filter/Paging (`/events`)
  - API: `GET /api/events` mit `source`, `level`, `limit`, `offset`

## Datenbank
- Beim Start erzeugt die App automatisch alle benötigten Tabellen (SQLite Datei `genapp.db`).
- Zurücksetzen (alle Daten verwerfen): App stoppen und `genapp.db` löschen, dann neu starten.
- Alternativ:
  - `python scripts/cleanup_and_migrate.py` entfernt die SQLite-Datei und erzeugt das Schema neu.
  - `python scripts/reset_and_seed.py` setzt die DB zurück und befüllt Beispiel-Daten (aus `cntl/` übertragen).

## Troubleshooting
- Paketfehler beim Start: Prüfe `pip install -r requirements.txt` und aktive venv.
- Datenbankzugriff: Stelle sicher, dass `DATABASE_URL` korrekt ist und der Pfad schreibbar ist.
- Schema-/Migrationsthemen: `python scripts/cleanup_and_migrate.py` sorgt für ein frisches Schema inkl. Index auf `policy_number`.
- 404 in UI: Prüfe die URL‑Pfadschreibung; API‑Routen sind in `/api/...` verfügbar.
- Für Tests: `pytest tests/test_wsim_flows.py` führt ein automatisiertes WSim-ähnliches Szenario aus.

## Nächste Schritte
- Siehe `api_reference.md` für eine kurze API-Referenz inkl. curl-Beispiele.
