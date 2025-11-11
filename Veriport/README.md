# VeriPort

VeriPort ist ein einzelnes Python-Skript unter der GPL 3.0 Lizenz, das mit Hilfe von CrewAI-Agenten Quellcode von einer Sprache in eine andere überführt und jede Konvertierung durch einen automatisierten Review-Lauf gegenprüfen lässt. Das Tool eignet sich für kleine Experimente ebenso wie für wiederholbare Umsetzungen einzelner Dateien ohne komplettes Projekt-Setup.

## Zweck und Grundidee
1. Eingabedatei wählen (`python veriport.py <datei>`).
2. Ein „Converter“-Agent erzeugt Zielcode in der gewünschten Sprache.
3. Ein „Reviewer“-Agent vergleicht Original und Konvertat auf Funktionsgleichheit und Syntax.
4. Bei Ablehnung fließt das Feedback in die nächste Iteration ein (max. `--max-iters`).
5. Sobald der Review „approve“ liefert, schreibt VeriPort die konvertierte Datei auf die Platte.

Das Ergebnis ist dadurch reproduzierbarer als ein einmaliger Chat-Export, weil dieselbe Pipeline mehrfach verwendbar ist und klare Erfolgskriterien besitzt.

## Frameworks & Abhängigkeiten
- **Python 3.12** (siehe Hinweis in `requirements.txt`).
- **CrewAI** (`crewai==1.4.1`): Stellt `Agent`, `Task`, `Crew`, `Process` bereit. Beide Agents laufen darin sequenziell.
- **LangChain OpenAI** (`langchain-openai==1.0.2`): Wird automatisch als Fallback-Library genutzt, falls CrewAI keinen eigenen LLM-Wrapper findet. Erwartet `OPENAI_API_KEY` in der Umgebung oder `.env`.
- **python-dotenv** (`python-dotenv==1.2.1`): Optional. Wird beim Start geladen, um API-Keys oder Modelle aus `.env` zu beziehen.
- Standardbibliothek (`argparse`, `pathlib`, `dataclasses`, `json`, `re`, `os`, `sys`).

> Installationsempfehlung: `python -m pip install -r requirements.txt` in einer Python-3.12-Umgebung.

## Aufbau und Datenfluss
- `_build_llm()` versucht zuerst, den CrewAI-LLM zu initialisieren; fällt sonst auf `ChatOpenAI` zurück.
- `_make_converter_agent()` / `_make_reviewer_agent()` definieren Rolle, Ziel und Backstory der Agents.
- `_make_conversion_task()` liefert die Prompt-Schablone für die Konvertierung. Sie enthält Originalcode, eventuelles Feedback und zwingt reine Codeausgabe.
- `_make_review_task()` fordert eine JSON-Antwort mit `verdict` (`approve|revise`) und kurzen Hinweisen.
- `_safe_json_extract()` entfernt ggf. Code-Fences und zieht das erste JSON-Objekt aus einer LLM-Antwort.
- `ConverterPipeline.iterate()` setzt alles zusammen: Konvertieren → Review → ggf. nächste Runde, bis genehmigt oder Iterationslimit erreicht ist.
- `resolve_output_path()` ersetzt die Dateiendung oder fügt `.converted.<ext>` an, falls Input- und Zielendung gleich sind.
- `main()` stellt die CLI bereit, liest Dateien ein, startet die Pipeline und übernimmt Dateischreibrechte.

## CLI-Aufruf
```
python veriport.py <quelle> [--target-lang sprache] [--ext endung]
                    [--model name] [--max-iters n]
                    [--verbose] [--dry-run]
```

| Option | Bedeutung |
| --- | --- |
| `input` | Pflicht. Pfad zur umzuwandelnden Datei. |
| `--target-lang`, `-l` | Zielsprachenname (Standard: `python`). Bestimmt auch die Agentenprompts. |
| `--ext` | Erzwingt eine konkrete Dateiendung (z. B. `ts`). Wenn leer, wird sie aus der Sprache abgeleitet. |
| `--model`, `-m` | OpenAI-Modellname für beide Agents (Standard: `gpt-5`). |
| `--max-iters` | Anzahl Konvertierungs-/Review-Schleifen (Standard: 3). |
| `--verbose`, `-v` | Übergibt `verbose=True` an CrewAI und zeigt Agentendialoge. |
| `--dry-run` | Führt den gesamten Ablauf aus, schreibt aber keine Datei – praktisch für schnelle Checks. |

## Beispiele
- **Quickstart mit den Dateien unter `example/`:**
  ```bash
  # erzeugt example/hello.py aus example/hello.c (die Logausgabe landet auf STDOUT)
  python veriport.py example/hello.c --target-lang python --verbose
  ```
  Die erstellte `example/conversion.txt` zeigt einen vollständigen CLI-Lauf inklusive Reviewer-Logs. Sie eignet sich als Referenz, wie ein erfolgreicher Durchgang aussehen soll.
- **JavaScript nach Python, Datei schreiben:**
  ```bash
  OPENAI_API_KEY=sk-... python veriport.py src/handler.js --target-lang python --model gpt-4o
  ```
- **TypeScript nach Go, nur prüfen:**
  ```bash
  python veriport.py service.ts --target-lang go --dry-run --max-iters 5
  ```

Nach erfolgreicher Genehmigung meldet das Tool: `Conversion approved after <n> attempt(s)` und gibt den Ausgabepfad aus.

## Tipps & Fehlersuche
- Ohne gesetzten `OPENAI_API_KEY` erscheint eine Warnung und CrewAI/LangChain schlagen spätestens beim ersten LLM-Aufruf fehl. Schlüssel daher vorab exportieren oder in `.env` eintragen.
- Scheitert der Reviewer mehrfach, prüfe das Feedback (wird im Terminal ausgegeben) und erhöhe bei Bedarf `--max-iters` oder passe den Eingabetext manuell an.
- Nutze `--ext`, wenn die automatische Zuordnung deiner Zielsprache nicht existiert oder anders lauten soll.

Damit hast du einen schnellen Überblick, wie `veriport.py` funktioniert, welche Bibliotheken beteiligt sind und wie der Aufruf gelingt.
