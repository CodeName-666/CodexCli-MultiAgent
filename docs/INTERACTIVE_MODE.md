# Interaktiver Modus - Multi-Agent Codex

## Überblick

Der interaktive Modus macht die Verwendung von Multi-Agent Codex einfacher und benutzerfreundlicher.
Anstatt alle Parameter als Kommandozeilen-Argumente anzugeben, führt dich der interaktive Modus
durch alle notwendigen Schritte.

## Verwendung

### Einfachster Start

```bash
python multi_agent_codex.py
```

oder explizit:

```bash
python multi_agent_codex.py run
```

## Ablauf

### Schritt 1: Familie auswählen

Der interaktive Modus zeigt dir alle verfügbaren Agent-Familien:

```
Verfügbare Familien:
  1. developer
  2. designer
  3. qa

Wähle Familie (Nummer oder Name):
```

Du kannst entweder:
- Eine Nummer eingeben (z.B. `1`)
- Einen Namen eingeben (z.B. `developer`)

### Schritt 2: Task beschreiben

Gib eine Beschreibung der Aufgabe ein. Mehrere Zeilen sind möglich:

```
--- Task-Beschreibung ---
Gib eine Beschreibung der Aufgabe ein (mehrere Zeilen möglich).
Beende Eingabe mit einer leeren Zeile.

> Implementiere eine neue User-Authentifizierung
> mit JWT-Tokens und Session-Management
>
```

Beende die Eingabe mit einer leeren Zeile (Enter).

### Schritt 3: Optionen konfigurieren

Der Modus fragt nach wichtigen Optionen:

1. **Working Directory**: In welchem Verzeichnis soll gearbeitet werden?
   - Standard: `.` (aktuelles Verzeichnis)

2. **Auto-Apply**: Sollen Diffs automatisch angewendet werden?
   - `y` = Ja, `N` = Nein (Standard)

3. **Apply-Modus** (wenn Auto-Apply aktiviert):
   - `end`: Nur am Ende alle Diffs anwenden
   - `role`: Nach jeder Rolle Diffs anwenden

4. **Apply-Confirm**: Vor jedem Apply bestätigen?
   - `y` = Ja, `N` = Nein (Standard)

5. **Fail-Fast**: Bei Fehler sofort abbrechen?
   - `y` = Ja, `N` = Nein (Standard)

6. **Task-Splitting**: Große Tasks automatisch aufteilen?
   - `y` = Ja, `N` = Nein (Standard)

### Schritt 4: Zusammenfassung & Bestätigung

Der Modus zeigt eine Zusammenfassung aller Einstellungen:

```
============================================================
ZUSAMMENFASSUNG
============================================================
Familie:      developer
Task:         Implementiere eine neue User-Authentifizierung...
Verzeichnis:  .
Auto-Apply:   Ja
  - Modus:    end
  - Confirm:  Nein
Fail-Fast:    Nein
Task-Split:   Nein
============================================================

Task starten? (Y/n):
```

Bestätige mit `Y` oder Enter, um zu starten.

### Schritt 5: Ausführung

Die Multi-Agent-Pipeline startet:

```
============================================================
STARTE MULTI-AGENT PIPELINE
============================================================

[Architect] Starting...
[Architect] Output gespeichert in: runs/20240101_120000/architect/
...
```

## Beispiel-Session

```bash
$ python multi_agent_codex.py

=== Multi-Agent Codex - Interactive Mode ===

Verfügbare Familien:
  1. developer
  2. designer

Wähle Familie (Nummer oder Name): 1
✓ Gewählt: developer

--- Task-Beschreibung ---
Gib eine Beschreibung der Aufgabe ein (mehrere Zeilen möglich).
Beende Eingabe mit einer leeren Zeile.

Füge Logging zur process_data() Funktion hinzu

✓ Task: Füge Logging zur process_data() Funktion hinzu

--- Optionen ---
Working Directory (default: .):
Diff automatisch anwenden? (y/N): y
Apply-Modus (end/role, default: end):
Vor jedem Apply bestätigen? (y/N):
Bei Fehler sofort abbrechen? (y/N):
Task-Splitting aktivieren? (y/N):

============================================================
ZUSAMMENFASSUNG
============================================================
Familie:      developer
Task:         Füge Logging zur process_data() Funktion hinzu
Verzeichnis:  .
Auto-Apply:   Ja
  - Modus:    end
  - Confirm:  Nein
Fail-Fast:    Nein
Task-Split:   Nein
============================================================

Task starten? (Y/n):

============================================================
STARTE MULTI-AGENT PIPELINE
============================================================

[Pipeline startet...]
```

## Vorteile des interaktiven Modus

### ✅ Einfacher für Einsteiger
- Keine komplexen Kommandozeilen-Argumente merken
- Geführter Prozess durch alle Optionen
- Klare Erklärungen bei jedem Schritt

### ✅ Weniger Fehler
- Validierung der Eingaben
- Zusammenfassung vor Ausführung
- Bestätigungsschritt verhindert versehentliche Starts

### ✅ Schneller bei wiederholter Nutzung
- Sinnvolle Defaults für die meisten Optionen
- Schnelles Durchklicken mit Enter für Standardwerte

### ✅ Übersichtlicher
- Klare Struktur des Prozesses
- Zusammenfassung aller Einstellungen
- Besseres Verständnis der verfügbaren Optionen

## Rückwärtskompatibilität

Der alte CLI-Modus mit `--task` funktioniert weiterhin:

```bash
python multi_agent_codex.py --task "Implementiere Feature X" --apply
```

## Vergleich: Alt vs. Neu

### Alter Modus (weiterhin verfügbar)
```bash
python multi_agent_codex.py \
  --config agent_families/developer_main.json \
  --task "Implementiere User Auth" \
  --apply \
  --apply-mode end \
  --dir .
```

**Vorteile:**
- Scriptbar
- Für CI/CD geeignet
- Schnell wenn man Parameter kennt

**Nachteile:**
- Komplex für Einsteiger
- Viele Parameter zu merken
- Fehleranfällig

### Neuer interaktiver Modus
```bash
python multi_agent_codex.py
```

**Vorteile:**
- Einfach zu bedienen
- Keine Parameter merken
- Geführter Prozess
- Validierung & Bestätigung

**Nachteile:**
- Nicht scriptbar (aber dafür gibt's den alten Modus)
- Etwas langsamer (wegen Interaktion)

## Wann welchen Modus nutzen?

### Nutze den interaktiven Modus wenn:
- ✅ Du neu im Tool bist
- ✅ Du eine Ad-hoc-Aufgabe hast
- ✅ Du unsicher über die richtigen Parameter bist
- ✅ Du eine Zusammenfassung vor dem Start sehen willst

### Nutze den CLI-Modus wenn:
- ✅ Du in Scripts/CI/CD automatisieren willst
- ✅ Du die Parameter genau kennst
- ✅ Du maximale Geschwindigkeit brauchst
- ✅ Du von anderen Tools aufrufst

## Shortcuts & Tipps

### Schnelles Durchklicken
- Drücke einfach Enter für Standardwerte
- Die meisten Optionen haben sinnvolle Defaults

### Familie-Auswahl
- Gib nur den ersten Buchstaben ein (z.B. `d` für `developer`)
- Oder die Nummer (schneller)

### Multi-Line Tasks
- Nutze mehrere Zeilen für komplexe Aufgaben
- Strukturiere mit Bullet-Points für Klarheit
- Leere Zeile = Ende der Eingabe

### Abbrechen
- `Ctrl+C` um jederzeit abzubrechen
- Bei "Task starten?" kannst du mit `n` abbrechen

## Fehlerbehandlung

### "Keine Agent-Familien gefunden"
**Problem:** Das `agent_families/` Verzeichnis ist leer.

**Lösung:** Erstelle zuerst eine Familie:
```bash
python multi_agent_codex.py create-family --description "Dein Team"
```

### "Familie nicht gefunden"
**Problem:** Tippfehler oder Familie existiert nicht.

**Lösung:** Wähle eine Familie aus der Liste per Nummer.

### "Keine Task-Beschreibung angegeben"
**Problem:** Du hast sofort Enter gedrückt ohne Task-Text.

**Lösung:** Gib mindestens eine Zeile Text ein, dann leere Zeile.

## Weitere Ressourcen

- [Multi-Agent Codex README](../README.md)
- [Create-Family Guide](CREATE_FAMILY.md)
- [Create-Role Guide](CREATE_ROLE.md)
- [Configuration Guide](CONFIGURATION.md)
