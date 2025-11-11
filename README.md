#dav_ag_ki

Dieses Repository bündelt drei voneinander unabhängige Beispiele und Tools, die im Rahmen der Arbeit der Arbeitsgruppe Einsatz von GenAI im Aktuariat der DAV (Deutsche Aktuarvereinigung) erstellt wurden. Fragen zum Repo oder den Inhalten bitte an den REPO-Owner richten.

| Ordner | Kurzbeschreibung | Primäre Technologien |
| --- | --- | --- |
| `IBM GenApp Python/` | Python/ FastAPI-Port einer historischen IBM GenApp COBOL-Anwendung inklusive UI, REST-APIs, SQLite-DB, Seed-Skripten und Dokumentation. | FastAPI, SQLAlchemy, Jinja2, SQLite |
| `Quicksort/` | Bewusst komplizierte Quicksort-Implementierung in C, gedacht als einfacher Benchmark für Code-Verständnis und Dokumentation (Beschreibung siehe `kowabunga.md`). | ANSI C |
| `Veriport/` | Einzeldatei-CLI, die mit CrewAI Agents Code in neue Sprachen übersetzt und automatisch reviewt; enthält ein Beispiel in `example/`. | Python 3.12, CrewAI, LangChain |

Weiterführende Informationen, Installationsschritte und Architekturhinweise findest du jeweils in den README-Dateien der Unterordner.

## Lizenzübersicht

| Ordner | Lizenz | Datei |
| --- | --- | --- |
| `IBM GenApp Python/` | Eclipse Public License 2.0 | `IBM GenApp Python/LICENSE.md` |
| `Quicksort/` | Apache License 2.0 | `Quicksort/LICENSE.md` |
| `Veriport/` | GNU GPL v3 oder später | `Veriport/LICENSE.md` |

Bitte beachte die entsprechenden NOTICE-Dateien (`IBM GenApp Python/notice.md`, `Veriport/notice.md`) für Drittanbieterkomponenten sowie Hinweise in den jeweiligen READMEs. Eine gemeinsame Root-Lizenz existiert nicht; jedes Teilprojekt bewahrt seine eigene Lizenzierung und darf nur unter deren Bedingungen weitergegeben oder kombiniert werden.

## Schnellstart pro Projekt

### IBM GenApp Python
1. In den Ordner wechseln: `cd "IBM GenApp Python"`.
2. Virtuelle Umgebung für Python 3.10+ (empfohlen 3.11) erstellen und aktivieren.
3. Abhängigkeiten installieren: `pip install -r requirements.txt`.
4. Optional `.env.example` kopieren und `DATABASE_URL` anpassen.
5. Server starten: `uvicorn app.main:app --reload`.

Details zu APIs, Seeds (`scripts/cleanup_and_migrate.py`, `scripts/reset_and_seed.py`) und Architektur stehen in `IBM GenApp Python/README.md` sowie im `docs/`-Ordner (`first_steps.md`, `api_reference.md`, `portierung_doku.md`). Rechtliche Hinweise sind in `LICENSE.md` (EPL-2.0) und `notice.md` zusammengefasst.

### Quicksort
1. In den Ordner wechseln: `cd Quicksort`.
2. Datei kompilieren, z. B. `cc -std=c99 -Wall -Wextra kowabunga_spaghetti.c -o kowabunga`.
3. Programm mit einer Liste von Ganzzahlen aufrufen und die Sortierung prüfen.

Der Hintergrund zur „kowabunga“-Variante steht in `Quicksort/README.md`, die Lizenz in `Quicksort/LICENSE.md` (Apache License 2.0).

### VeriPort
1. Python 3.12 einsetzen (Versionshinweis in `Veriport/requirements.txt`).
2. `cd Veriport && python -m venv .venv && source .venv/bin/activate`.
3. `pip install -r requirements.txt`.
4. `OPENAI_API_KEY` setzen (direkt in der Shell oder via `.env`).
5. Beispiel ausführen: `python veriport.py example/hello.c --target-lang python`.

Die CLI, Agenten und Beispiel-Logs (`example/conversion.txt`) sind in `Veriport/README.md` beschrieben. Die Software steht unter GPL-3.0-or-later (`Veriport/LICENSE.md`), zusätzliche Hinweise in `Veriport/notice.md`.

## Beiträge & Issues

Änderungen sollten jeweils im passenden Unterordner erfolgen. Prüfe vor Pull-Requests die dort dokumentierten Tests (z. B. `pytest` unter `IBM GenApp Python/`, GCC-Builds unter `Quicksort/`, CrewAI-Läufe unter `Veriport/`). Fragen zu einzelnen Komponenten bitte mit Verweis auf den betreffenden Ordner stellen.
