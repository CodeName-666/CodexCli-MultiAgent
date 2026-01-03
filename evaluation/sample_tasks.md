# Sample Tasks für Multi-Agent Evaluation

## Kategorie A: Einfache Aufgaben (5-10 Min)

### A1: Bug Fix - Type Error
**Aufgabe:**
```
In der Datei 'utils/string_helpers.py' gibt es eine Funktion 'format_name(first, last)',
die einen TypeError wirft wenn None übergeben wird.
Behebe den Bug und füge eine Validierung hinzu.
```

**Akzeptanzkriterien:**
- Funktion akzeptiert None-Werte
- Gibt sinnvollen Standardwert zurück
- Keine Breaking Changes für existierenden Code

**Erwartete Änderungen:**
- 1 Datei modifiziert
- ~5-10 Zeilen Code

---

### A2: Feature - Logging hinzufügen
**Aufgabe:**
```
Füge Logging zur Funktion 'process_data()' in 'core/processor.py' hinzu.
Logge Start, Ende und eventuelle Fehler.
```

**Akzeptanzkriterien:**
- Verwendet Python logging module
- Info-Level für normale Operation
- Error-Level für Exceptions
- Keine Performance-Degradation

**Erwartete Änderungen:**
- 1 Datei modifiziert
- ~10-15 Zeilen Code

---

### A3: Refactoring - Umbenennung
**Aufgabe:**
```
Benenne die Funktion 'calc()' in 'calculate_total()' um und aktualisiere
alle Referenzen im gesamten Projekt.
```

**Akzeptanzkriterien:**
- Alle Referenzen aktualisiert
- Tests laufen weiterhin
- Keine toten Referenzen

**Erwartete Änderungen:**
- 3-5 Dateien modifiziert
- ~20-30 Zeilen Code

---

## Kategorie B: Mittlere Aufgaben (15-30 Min)

### B1: API Endpoint - User Info
**Aufgabe:**
```
Erstelle einen neuen REST-Endpoint GET /api/user/{id} der Benutzerinformationen
zurückgibt. Inkludiere Input-Validierung und Fehlerbehandlung.
```

**Akzeptanzkriterien:**
- Endpoint funktioniert
- Validiert ID-Parameter
- Gibt 404 bei nicht gefundenem User
- Gibt 400 bei invalider ID
- Gibt 200 + JSON bei Erfolg
- Mindestens 2-3 Unit Tests

**Erwartete Änderungen:**
- 1-2 neue Dateien (endpoint + tests)
- ~50-100 Zeilen Code

---

### B2: Komponente - Cache Manager
**Aufgabe:**
```
Implementiere eine CacheManager-Klasse mit Methoden get(), set(), delete()
und has(). Nutze ein Dictionary als Backend. Füge TTL-Support hinzu.
```

**Akzeptanzkriterien:**
- Alle CRUD-Operationen funktionieren
- TTL wird korrekt behandelt (abgelaufene Einträge entfernt)
- Thread-safe (optional)
- Mindestens 5 Unit Tests
- Docstrings vorhanden

**Erwartete Änderungen:**
- 1 neue Datei für Klasse
- 1 neue Datei für Tests
- ~100-150 Zeilen Code total

---

### B3: Integration - Email Service
**Aufgabe:**
```
Integriere einen Email-Service in die existierende User-Registration.
Sende Welcome-Email nach erfolgreicher Registrierung.
```

**Akzeptanzkriterien:**
- Email wird versendet (oder gemockt in Tests)
- Fehler beim Email-Versand brechen Registrierung nicht ab
- Email-Template anpassbar
- Tests für Success- und Failure-Szenarien

**Erwartete Änderungen:**
- 2-3 Dateien modifiziert
- 1 neue Datei für Email-Service
- 1 neue Datei für Tests
- ~150-200 Zeilen Code

---

## Kategorie C: Komplexe Aufgaben (30-60 Min)

### C1: Feature-Set - User Authentication
**Aufgabe:**
```
Implementiere komplettes User-Authentication-System:
- Login (POST /api/auth/login)
- Logout (POST /api/auth/logout)
- Session-Management
- Token-basiert (JWT)
```

**Akzeptanzkriterien:**
- Alle Endpoints funktionieren
- Tokens werden korrekt generiert und validiert
- Sessions persistent (oder in-memory mit Ablauf)
- Password-Hashing (bcrypt/argon2)
- Mindestens 10 Unit Tests
- Error-Handling für alle Edge Cases
- Dokumentation (API-Docs oder README)

**Erwartete Änderungen:**
- 3-5 neue Dateien
- 2-3 modifizierte Dateien
- ~300-500 Zeilen Code

---

### C2: Architektur - Service Layer
**Aufgabe:**
```
Refactore die monolithische app.py in eine Service-Layer-Architektur:
- Routers (API-Layer)
- Services (Business Logic)
- Repositories (Data Access)
- Models (Data Structures)
```

**Akzeptanzkriterien:**
- Klare Trennung der Concerns
- Alle Tests laufen weiterhin
- Keine Funktionalitätsverluste
- Verbesserte Testbarkeit
- Dokumentation der neuen Struktur

**Erwartete Änderungen:**
- 5-10 neue Dateien
- 3-5 modifizierte Dateien
- ~500-800 Zeilen Code (inkl. Verschiebungen)

---

### C3: Full-Stack - Todo App
**Aufgabe:**
```
Erstelle eine einfache Todo-App:
- Backend: REST-API (CRUD für Todos)
- Frontend: Simple HTML/JS UI
- Tests: Backend Unit Tests + Integration Tests
- Datenbank: SQLite oder In-Memory
```

**Akzeptanzkriterien:**
- CRUD funktioniert (Create, Read, Update, Delete)
- Frontend kann mit Backend kommunizieren
- Responsive UI (Basic)
- Mindestens 15 Tests
- README mit Setup-Anleitung

**Erwartete Änderungen:**
- 8-12 neue Dateien
- ~800-1200 Zeilen Code

---

## Verwendung

### Schritt 1: Aufgabe auswählen
Wähle eine Aufgabe passend zum Komplexitätslevel, den du testen möchtest.

### Schritt 2: Baseline erstellen
Erstelle einen separaten Branch oder verwende ein Test-Repository.

### Schritt 3: Beide Ansätze testen

**Option A: Multi-Agent**
```bash
python evaluation/run_evaluation.py --interactive
# Wähle "Multi-Agent"
# Führe Task aus mit: python multi_agent_codex.py --family developer --task "..."
```

**Option B: Direkte CLI**
```bash
python evaluation/run_evaluation.py --interactive
# Wähle "Direct CLI"
# Führe Task aus mit normaler CLI-Interaktion
```

### Schritt 4: Ergebnisse vergleichen
```bash
python evaluation/run_evaluation.py --compare <task_name>
```

## Tipps für faire Tests

1. **Gleiche Ausgangslage**: Beide Ansätze starten vom gleichen Code-Stand
2. **Gleiche Ressourcen**: Keine Unterbrechungen, gleiche Tageszeit
3. **Gleiche Ziele**: Beide müssen die gleichen Akzeptanzkriterien erfüllen
4. **Mehrere Durchläufe**: Am besten 2-3 Mal testen für Konsistenz
5. **Dokumentieren**: Notiere Beobachtungen während der Tests

## Erwartete Erkenntnisse

Nach den Tests solltest du beantworten können:

- **Wann** ist Multi-Agent besser? (Vermutung: komplexe, mehrstufige Tasks)
- **Wann** ist CLI besser? (Vermutung: einfache, fokussierte Tasks)
- **Qualitätsunterschied**: Liefert Multi-Agent konsistent bessere Qualität?
- **Kosten-Nutzen**: Rechtfertigt die Qualität die höheren Kosten?
- **Use Cases**: Für welche Szenarien würdest du welchen Ansatz empfehlen?
