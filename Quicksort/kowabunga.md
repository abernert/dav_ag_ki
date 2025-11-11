# Dokumentation zu `kowabunga_spaghetti.c`

## Ueberblick
- `kowabunga_spaghetti` sortiert ein Feld von `int`-Werten in aufsteigender Reihenfolge.
- Das Programm kapselt alle Hilfsdaten in einer `Ctx`-Struktur (Array, Laenge, Zufalls-Seed, Vergleichsfunktion, Debug-Feld `chaos`).
- Drei leicht unterschiedliche QuickSort-Varianten (`Q1`, `Q2`, `Q3`) teilen sich dieselbe Partitionierlogik, werden aber zufaellig gewechselt, um absichtlich "spaghetti"-artige Aufrufe zu erzeugen.
- Kleine Teilbereiche (weniger als 16 Elemente) werden per Einfuege-Sortierung bearbeitet, weil sie dabei schneller und stabiler fertig werden.

## Bausteine im Detail
### Struktur `Ctx`
| Feld   | Zweck |
| ------ | ----- |
| `int *a` | Zeiger auf das zu sortierende Feld. |
| `long n` | Anzahl der Elemente. |
| `volatile unsigned long chaos` | Spielwiese fuer die verschiedenen QuickSort-Varianten; beeinflusst die Daten nicht. |
| `long seed` | Startwert fuer den Linear-Congruential-Generator (LCG). |
| `int (*cmp)(const int*, const int*)` | Optionale Vergleichsfunktion; Standard ist `cmp_default` (aufsteigend). |

### Vergleich und Zufall
- `cmp_default` gibt -1, 0 oder 1 zurueck und nutzt die natuerliche Ordnung von `int`.
- `lcg` aktualisiert den Seed (`seed = seed * 1664525 + 1013904223`) und liefert pseudozufaellige Bits. Die QuickSort-Varianten verwenden zwei unterschiedliche Formeln, damit sich die Rekursionen sichtbar unterscheiden.

### `ins_sometimes`
- Klassische Einfuege-Sortierung fuer einen Bereich `[L, R]`.
- Wird immer dann genutzt, wenn der Bereich kuerzer als 16 Elemente ist; das vermeidet tiefe Rekursion und verbessert die Cache-Lokalitaet.

### `partition_like`
1. Waehlt einen Pivot ueber Median-of-three: erstes, mittleres und letztes Element werden sortiert (`PIVOT_MAGIC`).
2. Tauscht den Pivot an die Mittelposition `m` und vergleicht dann zwei Zeiger `i` (links) und `j` (rechts).
3. Elemente kleiner als der Pivot wandern nach links, groessere nach rechts; Gleichheit fuehrt zu keinem weiteren Tausch.
4. Je nach Paritaet der Indizes verwendet der Code entweder eine XOR-Vertauschung oder normales Tauschen (`SWAPi`). Technisch hat das keinen praktischen Unterschied, es betont nur den "Spaghetti"-Charakter.
5. Rueckgabe sind die neuen Grenzen `out_i` und `out_j` fuer die verbleibenden Teilbereiche.

## Die drei QuickSort-Varianten
| Funktion | Spezielle Idee |
| -------- | -------------- |
| `Q1` | Klassischer QuickSort: prueft Basisfaelle, partitioniert und ruft dann zufaellig eine der drei Varianten auf beide Seiten auf (LCG-gestuetzt). |
| `Q2` | Gleicher Grundablauf, aber mit `switch`-Auswahl der Basisfaelle und einem anderen LCG (glibc-Variante). Ausserdem wird das `chaos`-Feld via XOR modifiziert, sobald ein Bereich fertig ist. |
| `Q3` | Arbeitet mit `goto`-Bloecken, um den rechten Rekursionszweig zu entrollen. Der linke Zweig ruft wiederum eine zufaellige Variante auf Basis von `chaos % 3` auf. |

Allen gemeinsam ist:
- Bereiche mit `L >= R` gelten als fertig.
- Bereiche mit weniger als 16 Elementen nutzen `ins_sometimes`.
- Die Reihenfolge bleibt identisch, unabhaengig davon, welche Variante gewaehlt wird; Unterschiede betreffen nur den Ablauf.

## Ablauf von `kowabunga_spaghetti`
1. `Ctx` wird auf Null gesetzt und mit Arrayzeiger, Laenge und Standard-Vergleich befuellt.
2. Der Seed kombiniert die Arrayadresse, die aktuelle Zeit und `n`, damit jedes Programmstart andere Rekursionspfade waehlt.
3. Aus dem Seed wird eine der drei QuickSort-Varianten als Startpunkt bestimmt (`(seed >> 3) % 3`).
4. Nach dem Sortieren wird das Array ueber einen `volatile` Zeiger angeruehrt (`*vp += 0;`). Das verhindert, dass aggressive Compiler den gesamten Sortiervorgang wegen vermeintlicher Nichtbenutzung herausoptimieren.

## Demo-Programm (`#ifdef DEMO`)
- Liest Zahlen entweder aus den Programmargumenten oder aus `stdin` (beliebig viele Werte dank dynamischem Realloc).
- Ohne Eingabe nutzt es einen kleinen Beispiel-Array.
- Ruft `kowabunga_spaghetti` auf und druckt das Ergebnis mit Leerzeichen getrennt.

## Besonderheiten und Randfaelle
- `chaos` und die unterschiedlichen Zufallsquellen dienen nur dazu, die Implementierung verspielt aussehen zu lassen; sie beeinflussen das Resultat nicht.
- Der Code akzeptiert auch benutzerdefinierte Vergleichsfunktionen, wenn `ctx.cmp` ausserhalb der Datei gesetzt wuerde.
- Da Einfuege-Sortierung fuer kleine Bereiche genutzt wird, ist das Laufzeitverhalten fuer fast sortierte Arrays gut.
- Negative Zahlen, Duplikate und Nullwerte werden problemlos verarbeitet, weil alles ueber `int` und den Vergleich laeuft.

## Kurz gesagt
`kowabunga_spaghetti.c` ist ein bewusst verschraenktes, aber korrektes QuickSort, das viele Makros und Spruenge einsetzt. Wichtig fuer Anwender*innen: Mit `kowabunga_spaghetti(array, n)` erhalten sie ein aufsteigend sortiertes Array, ohne sich um die internen Spielereien kuemmern zu muessen.
