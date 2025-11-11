# Portierung Dokumentation – COBOL GenApp zu Python-Port

Diese Dokumentation fasst zusammen, welche COBOL-Funktionalitäten der GenApp-Anwendung in den Python-Port übertragen wurden, wie die Umsetzung erfolgt ist und welche Artefakte daraus hervorgegangen sind. Die Tabelle zu Beginn liefert einen Überblick über alle Bereiche; anschließend folgen detaillierte Beschreibungen.

## Übersichtstabelle

| Themenbereich | COBOL-Referenz | Python-Port Umsetzung | Artefakte / Pfade |
| --- | --- | --- | --- |
| Kundenanlage & Named Counter | `src/lgacdb01.cbl`, `src/lgacvs01.cbl`, `src/lgacdb02.cbl` | Service nutzt Counter-Tabelle, Security-Datensatz wird auto angelegt, optionale Rotation/Random-Passwords | `app/services/customers.py`, `app/db/models.py:Customer`, `app/api/routes_customers.py`
| Customer Security (Pass/State/Count) | `src/lgacdb02.cbl` | Default-Werte steuerbar via ENV; API für GET/PUT und Rotation vorhanden | `app/services/customers.py`, `app/api/routes_customers.py`
| Policen (Add/Update/Delete/Inquire) | `src/lgapdb01.cbl`, `src/lgipdb01.cbl`, `src/lgupdb01.cbl`, `src/lgdpol01.cbl` | Create & Update Services pro Typ, detailreiche Listen, ZIP-Filtern, transaktionale UI-Updates | `app/services/policies.py`, `app/api/routes_policies.py`, `app/templates/policies*.html`
| Policy Nummern & Commission | `cntl/db2cre.jcl` (Identity/Commission) | Globaler Counter `GENAPOLICYNUM`, Unique Index, Commission-Feld, Validierung | `app/services/policies.py`, `app/db/models.py`
| Claims (CRUD, KOMMAREA) | `src/lgicdb01.cbl`, `src/lgacus01.cbl`, Claims-Struktur in `lgcmarea.cpy` | REST API + UI mit GET/POST/PUT/Delete, Paging, Edit, Logging | `app/services/claims.py`, `app/api/routes_claims.py`, `app/templates/claim*.html`
| Fehler-/Returncode Mapping | COBOL Return Codes (00/01/70/88/89/90/98/99) | Zentrales Mapping, Exceptions → HTTP Problem Details | `app/utils/errors.py`, Nutzung in `app/api/routes_*`
| Logging/Monitoring (TSQ/TDQ) | `src/lgstsq.cbl`, TDQ `CSMT`, TSQ `GENAERRS` | Persistente `events`-Tabelle, UI/JSON API zum Browsen | `app/db/models.py:Event`, `app/services/*._log_event`, `app/api/routes_events.py`, `app/templates/events.html`
| Seed/Migration (cntl/JCL) | `cntl/db2cre.jcl`, Testdaten aus JCL Inserts | Skript verlagert die DDL/Seeds in Python, SQLite Reset & Seed | `scripts/reset_and_seed.py`, `data/seed_data.json`
| WSim Datenpools | `wsim/pcode.txt`, `wsim/fname.txt`, `wsim/sname.txt` | Lesen & Nutzen als Datenquellen + Faker Provider | `app/utils/datasets.py`, `app/utils/faker_providers.py`
| WSim Szenarien | `wsim/wsc*.txt` (SOAP/TSQ flows) | Integrationstest reproduziert WSim-Flow (Customer → Policy → Claim → Queries) | `tests/test_wsim_flows.py`
| Gesamtstart & Setup | Host SPOJ/Batch | `first_steps.md`, `.env`, `requirements.txt` (Faker/Pytest) | Aktualisierte Doku + Abhängigkeiten |

## Details nach Themenbereich

### 1. Kunden & Security
- **Named Counter Server (`GENACUSTNUM`)**: In COBOL über `Exec CICS Get Counter`. Python-Port nutzt Tabelle `counters` als Sequenzersatz (`app/services/customers.py:_next_counter`).
- **Security-Datensatz**: COBOL ruft `LGACDB02` und `LGACVS01`. Python-Port erstellt Security-Eintrag bei jedem Customer-Create (`_ensure_customer_security`). Default-Werte steuerbar via ENV (`GENAPP_SECURITY_MODE` = `static`, `random`, `rotate`).
- **Security-API**: `GET/PUT /api/customers/{id}/security`, Option `rotate=true` generiert neue Passwörter. Fehler werden über `CobolError` → `http_exception_for` gemappt.

### 2. Policen
- **Add Policy**: COBOL `LGAPDB01` + Typ-Insert (Motor/House/Commercial). Python-Port hat Services `create_policy`, `create_policy_motor`, etc. Schema `policy_number` ist non-null; Unique Index & Soft-Zähler gewährleisten Parität.
- **Inquire / ZIP-Filter**: `list_policies` & `list_policies_detailed` unterstützen `postcode`, Paging-Parameter. UI (`policies.html`) bietet Filter.
- **Update/Delete**: UI-Route `/policies/{id}/edit` führt Basis+Detail Update transaktional aus (`with db.begin()`); Service-Funktionen unterstützen `commit=False`, um Teilschritte im Sammel-Commit abzuschließen.
- **Fehlerverarbeitung**: COBOL Return Codes (01/70/90/98) werden durch `CobolError` abgebildet.

### 3. Claims
- **Model & API**: COBOL hat Claims via COMMAREA (`lgcmarea.cpy`). Python-Port: `app/db/models.py:Claim`, Services/Routes mit GET/POST/PUT/DELETE, UI `claims.html` (Filter/Paging), `claim_edit.html` zum Bearbeiten.
- **Tests**: WSim Flow test erstellt Claim & prüft Listen/Paging.

### 4. Fehlercodes & Logging
- **Error-Mapping**: Modul `app/utils/errors.py` enthält Return-Code-Tabelle, `CobolError`-Exception, `http_exception_for`.
- **Events**: Jede Service-Operation ruft `_log_event` (persistente `events`-Tabelle). UI `/events` + JSON `GET /api/events`.

### 5. Seed/Migration (`cntl/`)
- **Skript `reset_and_seed.py`**: Überträgt JCL-Insert-Daten in JSON (`data/seed_data.json`), erstellt DB neu, nutzt Services zum Einspielen.
- **`first_steps.md`**: Dokumentation ergänzt (Seed ausführen, Pytest WSim Flow).

### 6. WSim-Daten & Tests
- **Datenpools**: `datasets.py` liest `wsim`-Tabellen (Filter `*`-Kommentare). Faker Provider `genapp_first_name/last_name/postcode` verfügbar.
- **Integrationstest**: `tests/test_wsim_flows.py` simuliert SOAP/TSQ-Flows via REST (Customer → Motor Policy → Claim → Query). Nutzt Random-Daten aus `datasets`.
- **Optional Lasttests**: nicht umgesetzt, aber Struktur (TestClient, Faker) liefert Grundlage.

## Hinweise zur Nutzung
- Installationen: `pip install -r requirements.txt` (enthält FastAPI + Faker + Pytest).
- Start: `uvicorn app.main:app --reload` (aus `python_port/`), `.env` optional.
- Datenreset: `python scripts/reset_and_seed.py`.
- Tests: `pytest tests/test_wsim_flows.py` (nutzt isolierte SQLite).

## Fazit
Der Python-Port deckt die im COBOL-System bereitgestellten Geschäftsprozesse vollständig ab, mit automatisierter Security, detailreichen Policen-Funktionen, Claims-CRUD, Logging und Seeds/Tests. cntl- und wsim-Artefakte sind in Python-Äquivalente transformiert, sodass Entwicklung und Tests plattformunabhängig erfolgen können.
