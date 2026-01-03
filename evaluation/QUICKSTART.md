# Quick Start: Multi-Agent Evaluation

## Sofort loslegen in 3 Schritten

### 1. Test-Repository vorbereiten

Erstelle ein isoliertes Test-Projekt oder nutze einen separaten Branch:

```bash
# Option A: Neues Test-Repository
mkdir test-project
cd test-project
git init

# Erstelle eine einfache Python-Struktur
mkdir -p src/utils tests
touch src/__init__.py src/utils/__init__.py tests/__init__.py
```

### 2. Erste Testaufgabe durchführen

**Beispiel: Bug Fix Task (Einfach)**

```bash
# Erstelle Test-Datei mit absichtlichem Bug
cat > src/utils/string_helpers.py << 'EOF'
def format_name(first, last):
    """Format a full name."""
    return f"{first} {last}"
EOF

# Test-Datei
cat > tests/test_string_helpers.py << 'EOF'
from src.utils.string_helpers import format_name

def test_format_name():
    assert format_name("John", "Doe") == "John Doe"
    # This will fail with None values!
    assert format_name(None, "Doe") == "Doe"
    assert format_name("John", None) == "John"
EOF
```

**Aufgabe:** Behebe den Bug, damit die Funktion mit None-Werten umgehen kann.

### 3. Beide Ansätze testen

#### 3a. Test mit Multi-Agent

```bash
# Starte Evaluation
cd /path/to/Codex_CLI_Agent
python evaluation/run_evaluation.py --interactive

# Wenn gefragt:
# Task name: bug_fix_none_handling
# Approach: 1 (Multi-Agent)

# Dann führe aus:
python multi_agent_codex.py --family developer --task "Behebe Bug in format_name(): Funktion soll None-Werte akzeptieren und sinnvoll handhaben"

# Nach Fertigstellung:
# - Bewerte Ergebnisse im Evaluation Tool
# - Notiere Zeit, Qualität, etc.
```

#### 3b. Test mit direkter CLI

```bash
# Reset zum ursprünglichen Stand
git checkout src/utils/string_helpers.py

# Starte Evaluation
python evaluation/run_evaluation.py --interactive

# Wenn gefragt:
# Task name: bug_fix_none_handling
# Approach: 2 (Direct CLI)

# Dann nutze deine normale CLI:
claude-code  # oder dein CLI-Tool
# "Fix the format_name function to handle None values gracefully"

# Nach Fertigstellung:
# - Bewerte Ergebnisse im Evaluation Tool
```

#### 3c. Vergleiche Ergebnisse

```bash
python evaluation/run_evaluation.py --compare bug_fix_none_handling
```

---

## Empfohlener Testplan (30 Min Schnelltest)

Teste 3 Aufgaben unterschiedlicher Komplexität:

### Test 1: Einfach (10 Min total)
- **Aufgabe**: A1 - Bug Fix Type Error
- **Multi-Agent**: 5 Min
- **Direct CLI**: 5 Min

### Test 2: Mittel (15 Min total)
- **Aufgabe**: B2 - Cache Manager Komponente
- **Multi-Agent**: 7-8 Min
- **Direct CLI**: 7-8 Min

### Test 3: Komplex (Später, wenn Zeit)
- **Aufgabe**: C1 - User Authentication
- **Multi-Agent**: 30 Min
- **Direct CLI**: 30 Min

---

## Bewertungs-Checkliste

Nach jedem Test, bewerte:

### Code-Qualität (1-5)
- [ ] Ist der Code lesbar?
- [ ] Folgt er Best Practices?
- [ ] Ist er gut strukturiert?
- [ ] Gibt es Docstrings/Kommentare?

### Funktionalität (1-5)
- [ ] Erfüllt alle Akzeptanzkriterien?
- [ ] Funktioniert ohne Fehler?
- [ ] Edge Cases behandelt?
- [ ] Vollständig implementiert?

### Fehlerfreiheit (1-5)
- [ ] Keine Syntax-Fehler?
- [ ] Keine Laufzeit-Fehler?
- [ ] Tests laufen durch?
- [ ] Keine manuellen Fixes nötig?

### Test-Abdeckung (1-5)
- [ ] Tests vorhanden?
- [ ] Tests sinnvoll?
- [ ] Edge Cases getestet?
- [ ] Gute Abdeckung?

---

## Erwartete Ergebnisse

### Hypothesen zum Testen

**Multi-Agent sollte besser sein bei:**
- Komplexen, mehrstufigen Aufgaben
- Aufgaben mit mehreren Dateien
- Aufgaben die Review/Qualitätssicherung brauchen
- Systematische, reproduzierbare Ergebnisse

**Direct CLI sollte besser sein bei:**
- Einfachen, fokussierten Aufgaben
- Quick Fixes
- Explorative Arbeit
- Aufgaben mit viel Iteration

### Was misst du?

1. **Effizienz**: Ist Multi-Agent die Extra-Zeit wert?
2. **Qualität**: Liefert strukturierter Prozess bessere Ergebnisse?
3. **Konsistenz**: Sind Ergebnisse reproduzierbarer?
4. **Kosten**: Rechtfertigt Qualität höheren Token-Verbrauch?

---

## Nächste Schritte nach Schnelltest

1. **Analysiere Patterns**: Wo war welcher Ansatz besser?
2. **Dokumentiere Learnings**: Was hast du gelernt?
3. **Erweiterte Tests**: Teste komplexere Szenarien
4. **Optimierung**: Kann Multi-Agent-Config verbessert werden?
5. **Guidelines**: Erstelle Richtlinien: "Wann nutze ich was?"

---

## Troubleshooting

### "Multi-Agent dauert zu lange"
- **Lösung**: Reduziere Timeout-Werte in developer_main.json
- **Alternative**: Teste mit einfacheren Aufgaben zuerst

### "CLI-Ansatz inkonsistent"
- **Normal**: CLI ist interaktiver, daher variabler
- **Tipp**: Mehrere Durchläufe für statistisch relevante Daten

### "Kann Qualität nicht objektiv bewerten"
- **Lösung**: Nutze automatische Tests als Metrik
- **Tipp**: Lass einen Kollegen blind beide Ergebnisse bewerten

### "Brauche mehr Testaufgaben"
- **Siehe**: sample_tasks.md für 9 vordefinierte Aufgaben
- **Alternative**: Nutze echte Tasks aus deinem Backlog

---

## Support & Feedback

Wenn du Fragen hast oder Feedback zum Evaluation-Framework:
1. Check test_framework.md für Details
2. Check sample_tasks.md für mehr Aufgaben
3. Passe run_evaluation.py an deine Bedürfnisse an

Viel Erfolg beim Testen! 🚀
