# IBM GenApp Python

Portierung der IBM GenApp-Beispielanwendung von COBOL nach Python/FastAPI. Enthält ein vollständiges UI (Jinja2), REST-APIs, SQLite-Datenbankzugriff via SQLAlchemy sowie Hilfsskripte zum Befüllen und Testen. Detailbeschreibungen liegen im Ordner `docs/` (`first_steps.md`, `api_reference.md`, `portierung_doku.md`).

## Quelle

Die IBM GenApp COBOL-Quellen sind verfügbar unter: https://github.com/cicsdev/cics-genapp Sie stehen unter der Eclipse Public License 2.0.

## Projektstruktur
- `app/` – FastAPI-Anwendung inkl. Router (`api/`), Services, SQLAlchemy-Modelle (`db/`), Templates/Static Assets und Utils.
- `data/seed_data.json` – Ausgangsdaten für lokale Seeds (aus den Host-JCL-Inhalten übertragen).
- `scripts/cleanup_and_migrate.py` – löscht die lokale SQLite-Datei und erzeugt das Schema frisch.
- `scripts/reset_and_seed.py` – setzt die DB zurück und importiert Seed-Daten.
- `tests/test_wsim_flows.py` – Integrationstest, der den WSim-Flow (Customer → Policy → Claim → Queries) automatisiert.
- `docs/` – ergänzende Doku (Setup, API-Referenz, Portierungsdetails). Für vertiefte Infos dorthin verweisen.

## Voraussetzungen
- Python 3.10+
- `pip`, optional virtuelle Umgebung (`venv`)
- SQLite (im Lieferumfang von Python enthalten)

Siehe `docs/first_steps.md` für ausführliche Erläuterungen.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp env.example .env            # optional; Werte ggf. anpassen
uvicorn app.main:app --reload
```
- Standard-URL: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Für Hintergrundinfos (z. B. PYTHONPATH bei Unterordner-Start) siehe `docs/first_steps.md`.

## Datenbank & Seeds
- Default: `DATABASE_URL=sqlite:///./genapp.db` (siehe `env.example`).
- Tabellen werden beim Start automatisch erstellt; zusätzliche Runtime-Migrationen ergänzen `commission` und Indizes.
- Für ein sauberes Schema: `python scripts/cleanup_and_migrate.py`
- Für frische Demo-Daten: `python scripts/reset_and_seed.py` (nutzt `data/seed_data.json`).
- Detaillierte Portierungs- und DB-Infos: `docs/portierung_doku.md`.

## Tests
```bash
pytest tests/test_wsim_flows.py
```
Der Test deckt einen vollständigen Geschäftsfluss analog zu den WSim-Skripten ab und verifiziert REST-Endpunkte, Events und Datenpersistenz. Weitere Hinweise befinden sich in `docs/first_steps.md`.

## APIs & UI-Funktionen
- Kunden, Policen (inkl. Typ-spezifischer Endpunkte), Schäden und Events stehen als UI-Seiten und REST-APIs zur Verfügung.
- Beispielaufrufe, Parameter und Statuscodes sind in `docs/api_reference.md` dokumentiert.
- Umsetzung der COBOL-Funktionalitäten ist in `docs/portierung_doku.md` nach Themenbereichen nachvollziehbar.

## Weiterführende Dokumente (`docs/`)
1. `first_steps.md` – detaillierte Setup-Anleitung, Troubleshooting, Feature-Überblick.
2. `api_reference.md` – kompakte REST-Referenz mit curl-Beispielen.
3. `portierung_doku.md` – Mapping der COBOL-Module zu Python-Komponenten, inkl. Seeds, Logging und Tests.

Bitte diese Dokumente für weitere Details heranziehen.
