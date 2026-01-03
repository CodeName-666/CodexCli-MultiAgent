# Eigene Rollen erstellen

Ein vollständiger Guide zum Erstellen eigener Agent-Rollen für den Multi-Agent Codex CLI Orchestrator.

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Anatomie einer Rolle](#anatomie-einer-rolle)
3. [Quick Start](#quick-start)
4. [Prompt Engineering](#prompt-engineering)
5. [Rollen-Integration](#rollen-integration)
6. [Best Practices](#best-practices)
7. [Beispiele](#beispiele)
8. [Troubleshooting](#troubleshooting)

---

## Übersicht

Eine **Rolle** ist ein spezialisierter Agent mit einem klar definierten Zweck. Rollen werden als JSON-Dateien definiert und in der Hauptkonfiguration referenziert.

### Wann sollte ich eine neue Rolle erstellen?

✅ **Erstelle eine neue Rolle wenn:**
- Du eine neue Spezialisierung brauchst (z.B. "API Documentation Generator")
- Du einen bestehenden Agent anders konfigurieren willst
- Du eine neue Familie erstellen möchtest (z.B. "Marketing")

❌ **Erstelle KEINE neue Rolle wenn:**
- Du nur den Task ändern willst (nutze `--task` stattdessen)
- Du nur Parameter ändern willst (nutze Config-Overrides)

---

## Anatomie einer Rolle

### Minimale Rollen-Datei

```json
{
  "id": "my_role",
  "name": "My Custom Role",
  "role": "Specialist",
  "prompt_template": "{task}"
}
```

### Vollständige Struktur

```json
{
  "id": "security_auditor",
  "name": "Security Auditor",
  "role": "Security Expert",
  "prompt_template": "# SECURITY AUDIT\n\n## TASK\n{task}\n\n## CODEBASE\n{snapshot}\n\n## PREVIOUS FINDINGS\n{architect_output}\n\n## INSTRUCTIONS\nPerform a security audit focusing on:\n- SQL Injection vulnerabilities\n- XSS vulnerabilities\n- Authentication/Authorization issues\n- Cryptography misuse\n- Sensitive data exposure\n\nOutput format:\n```markdown\n# Security Audit Report\n\n## Critical Issues\n...\n\n## Medium Issues\n...\n\n## Recommendations\n...\n```"
}
```

### Feld-Beschreibungen

| Feld | Typ | Required | Beschreibung |
|------|-----|----------|--------------|
| `id` | string | ✅ | Eindeutige ID (muss mit Config `roles[].id` übereinstimmen) |
| `name` | string | ✅ | Lesbarer Name (für Logging) |
| `role` | string | ✅ | Rollen-Beschreibung (z.B. "Software Developer") |
| `prompt_template` | string oder string[] | ✅ | Das Prompt-Template mit Platzhaltern |

**Hinweis:** `prompt_template` kann auch als Array von Zeilen definiert werden, die zu einem String zusammengefügt werden.

```json
{
  "prompt_template": [
    "# TASK",
    "{task}",
    "",
    "# WORKSPACE",
    "{snapshot}"
  ]
}
```

---

## Quick Start

### Schritt 1: Rollen-Datei erstellen

Erstelle `agent_families/my_agents/translator.json`:

```json
{
  "id": "translator",
  "name": "Code Translator",
  "role": "Programming Language Expert",
  "prompt_template": "# CODE TRANSLATION\n\n## TASK\n{task}\n\n## SOURCE CODE\n{snapshot}\n\n## INSTRUCTIONS\nTranslate the code to the target language while:\n- Preserving functionality\n- Following target language idioms\n- Adding appropriate type hints/annotations\n- Maintaining code structure\n\nOutput as unified diff."
}
```

### Schritt 2: In Config einbinden

Erstelle `agent_families/translator_main.json`:

```json
{
  "system_rules": "Du bist ein Experte für Programmiersprachen.",
  "roles": [
    {
      "id": "translator",
      "file": "my_agents/translator.json",
      "instances": 1,
      "apply_diff": true
    }
  ],
  "final_role_id": "translator"
}
```

### Schritt 3: Ausführen

```bash
python multi_agent_codex.py \
  --config agent_families/translator_main.json \
  --task "Translate Python code to Rust"
```

**Das war's!** Deine Custom-Rolle ist einsatzbereit.

---

## Prompt Engineering

### Verfügbare Platzhalter

| Platzhalter | Wann verfügbar | Beispiel-Wert |
|-------------|----------------|---------------|
| `{task}` | Immer | "Implementiere User-Login" |
| `{snapshot}` | Immer | Workspace-Snapshot (Datei-Listings) |
| `{role_instance_id}` | Bei `instances > 1` | "1", "2", "3" |
| `{shard_id}` | Bei Sharding | "shard-1" |
| `{shard_title}` | Bei Sharding | "Feature A: User Authentication" |
| `{shard_goal}` | Bei Sharding | "Implement JWT-based auth" |
| `{allowed_paths}` | Bei Sharding | "app/auth/jwt.py, app/auth/tokens.py" |
| `{<role>_summary}` | Nach `<role>` | Kurz-Output (erste 500 Zeilen) |
| `{<role>_output}` | Nach `<role>` | Voller Output |

**Beispiel:** Nach Architect-Rolle sind verfügbar:
- `{architect_summary}` - Kurz-Version
- `{architect_output}` - Vollständig

### Template-Struktur

**Best Practice: Strukturiertes Template**

```json
{
  "prompt_template": "# [SECTION 1: CONTEXT]\n{context}\n\n# [SECTION 2: TASK]\n{task}\n\n# [SECTION 3: INPUTS]\n{inputs}\n\n# [SECTION 4: INSTRUCTIONS]\n{instructions}\n\n# [SECTION 5: OUTPUT FORMAT]\n{format}"
}
```

**Konkret:**

```json
{
  "prompt_template": "# CONTEXT\nYou are a {role}. Your expertise is in {expertise}.\n\n# TASK\n{task}\n\n# CODEBASE\n{snapshot}\n\n# PREVIOUS WORK\nArchitect's plan:\n{architect_summary}\n\n# INSTRUCTIONS\n1. Analyze the task and architecture\n2. Implement the solution\n3. Write tests\n\n# OUTPUT FORMAT\nProvide output as unified diff (git diff format):\n```diff\ndiff --git a/file.py b/file.py\n...\n```"
}
```

### Prompt-Strategie nach Rollen-Typ

#### 1. **Analyse-Rollen** (Architect, Reviewer)

**Ziel:** Verständnis und Planung

```json
{
  "prompt_template": "# ANALYSIS TASK\n{task}\n\n# CODEBASE\n{snapshot}\n\n# INSTRUCTIONS\nAnalyze and provide:\n1. Current state assessment\n2. Proposed solution architecture\n3. Implementation steps\n4. Potential risks\n\n# OUTPUT FORMAT\nMarkdown document with sections:\n- Overview\n- Architecture\n- Implementation Plan\n- Risks"
}
```

#### 2. **Implementierungs-Rollen** (Implementer, Designer)

**Ziel:** Konkrete Artefakte erstellen

```json
{
  "prompt_template": "# IMPLEMENTATION TASK\n{task}\n\n# ARCHITECTURE\n{architect_summary}\n\n# CODEBASE\n{snapshot}\n\n# INSTRUCTIONS\nImplement the solution following the architecture.\n\n# OUTPUT FORMAT\nUnified diff format:\n```diff\ndiff --git a/path/to/file.py b/path/to/file.py\n--- a/path/to/file.py\n+++ b/path/to/file.py\n@@ -10,5 +10,8 @@\n existing line\n+new line\n```"
}
```

#### 3. **Review-Rollen** (Tester, Security Auditor)

**Ziel:** Validierung und Feedback

```json
{
  "prompt_template": "# REVIEW TASK\n{task}\n\n# CODE TO REVIEW\n{implementer_output}\n\n# INSTRUCTIONS\nReview focusing on:\n- Correctness\n- Security\n- Performance\n- Best practices\n\n# OUTPUT FORMAT\nMarkdown report:\n## Passed\n- ...\n\n## Issues Found\n- ...\n\n## Recommendations\n- ..."
}
```

#### 4. **Integrations-Rollen** (Integrator, Summarizer)

**Ziel:** Zusammenfassung und Synthese

```json
{
  "prompt_template": "# INTEGRATION TASK\n{task}\n\n# ARTIFACTS\nArchitect:\n{architect_output}\n\nImplementer:\n{implementer_output}\n\nTester:\n{tester_output}\n\n# INSTRUCTIONS\nCreate final summary integrating all work.\n\n# OUTPUT FORMAT\n# Final Summary\n\n## Completed Work\n...\n\n## Test Results\n...\n\n## Next Steps\n..."
}
```

---

## Rollen-Integration

### In bestehende Pipeline einfügen

**Scenario:** Füge Security-Audit zwischen Implementer und Reviewer ein

**Vorher:**
```json
{
  "roles": [
    {"id": "architect", ...},
    {"id": "implementer", "depends_on": ["architect"], ...},
    {"id": "reviewer", "depends_on": ["implementer"], ...}
  ]
}
```

**Nachher:**
```json
{
  "roles": [
    {"id": "architect", ...},
    {"id": "implementer", "depends_on": ["architect"], ...},
    {"id": "security_auditor", "depends_on": ["implementer"], ...},
    {"id": "reviewer", "depends_on": ["security_auditor"], ...}
  ]
}
```

**Execution:**
```
architect → implementer → security_auditor → reviewer
```

### Parallele Rollen

**Scenario:** Parallele Review durch Security + Performance Experts

```json
{
  "roles": [
    {"id": "implementer", ...},
    {
      "id": "security_reviewer",
      "depends_on": ["implementer"],
      "file": "my_agents/security_reviewer.json"
    },
    {
      "id": "performance_reviewer",
      "depends_on": ["implementer"],
      "file": "my_agents/performance_reviewer.json"
    },
    {
      "id": "integrator",
      "depends_on": ["security_reviewer", "performance_reviewer"],
      "file": "developer_agents/integrator.json"
    }
  ]
}
```

**Execution:**
```
implementer
    ├─→ security_reviewer ─┐
    └─→ performance_reviewer ─┤
                              ↓
                          integrator
```

### Neue Familie erstellen

**Scenario:** Erstelle "Marketing" Familie

**1. Rollen definieren:**

`agent_families/marketing_agents/copywriter.json`:
```json
{
  "id": "copywriter",
  "name": "Marketing Copywriter",
  "role": "Content Creator",
  "prompt_template": "# COPYWRITING TASK\n{task}\n\n# BRAND GUIDELINES\n{snapshot}\n\n# INSTRUCTIONS\nCreate compelling marketing copy."
}
```

`agent_families/marketing_agents/seo_optimizer.json`:
```json
{
  "id": "seo_optimizer",
  "name": "SEO Specialist",
  "role": "SEO Expert",
  "prompt_template": "# SEO OPTIMIZATION\n{task}\n\n# CONTENT\n{copywriter_output}\n\n# INSTRUCTIONS\nOptimize for SEO."
}
```

**2. Familie konfigurieren:**

`agent_families/marketing_main.json`:
```json
{
  "system_rules": "Du bist ein Marketing-Experte.",
  "roles": [
    {
      "id": "copywriter",
      "file": "marketing_agents/copywriter.json"
    },
    {
      "id": "seo_optimizer",
      "file": "marketing_agents/seo_optimizer.json",
      "depends_on": ["copywriter"]
    }
  ],
  "final_role_id": "seo_optimizer"
}
```

**3. Nutzen:**
```bash
python multi_agent_codex.py \
  --config agent_families/marketing_main.json \
  --task "Create landing page copy for new product launch"
```

---

## Best Practices

### 1. Klare Rollen-Verantwortung

❌ **Schlecht:** Vage Rolle
```json
{
  "id": "helper",
  "name": "Helper",
  "role": "General Assistant",
  "prompt_template": "Help with: {task}"
}
```

✅ **Gut:** Spezifische Rolle
```json
{
  "id": "api_doc_generator",
  "name": "API Documentation Generator",
  "role": "Technical Writer specialized in API documentation",
  "prompt_template": "# API DOCUMENTATION\n\nGenerate OpenAPI/Swagger documentation for:\n{task}\n\nCode:\n{snapshot}"
}
```

### 2. Konsistente Output-Formate

**Definiere immer erwartetes Format:**

```json
{
  "prompt_template": "...\n\n# OUTPUT FORMAT\nProvide response as:\n\n```json\n{\n  \"summary\": \"...\",\n  \"issues\": [...],\n  \"recommendations\": [...]\n}\n```"
}
```

### 3. Context-Aware Prompts

**Nutze vorherige Outputs:**

```json
{
  "prompt_template": "# TASK\n{task}\n\n# ARCHITECTURE (from Architect)\n{architect_summary}\n\n# IMPLEMENTATION (from Implementer)\n{implementer_output}\n\n# YOUR ROLE\nReview the implementation against the architecture."
}
```

### 4. Sharding-Support

**Für Rollen mit `instances > 1`:**

```json
{
  "prompt_template": "# SHARD: {shard_title}\n\n## YOUR ASSIGNMENT\n{shard_goal}\n\n## TASK DETAILS\n{task}\n\n## ALLOWED FILES\nYou may ONLY modify:\n{allowed_paths}\n\n## INSTRUCTIONS\n- Focus ONLY on your shard: {shard_title}\n- Do NOT modify files outside allowed_paths\n- Coordinate with other instances via shared context"
}
```

### 5. Defensive Prompting

**Verhindere häufige Fehler:**

```json
{
  "prompt_template": "# TASK\n{task}\n\n# CRITICAL RULES\n- NEVER modify files you haven't read\n- ALWAYS use unified diff format\n- NEVER include explanatory text inside diff blocks\n- ALWAYS validate syntax before outputting\n\n# CODEBASE\n{snapshot}\n\n# OUTPUT FORMAT\n```diff\n[YOUR DIFF HERE]\n```"
}
```

---

## Beispiele

### Beispiel 1: Database Migration Generator

**Use Case:** Automatisches Erstellen von DB-Migrations basierend auf Model-Änderungen

**Rollen-Datei** (`agent_families/data_agents/migration_generator.json`):
```json
{
  "id": "migration_generator",
  "name": "Database Migration Generator",
  "role": "Database Expert",
  "prompt_template": "# DATABASE MIGRATION TASK\n\n## TASK\n{task}\n\n## CURRENT MODELS\n{snapshot}\n\n## PREVIOUS SCHEMA (if available)\n{architect_output}\n\n## INSTRUCTIONS\nGenerate database migration files:\n\n1. Analyze model changes\n2. Create migration script (SQL or ORM-specific)\n3. Include both upgrade() and downgrade() functions\n4. Add data migration if needed\n5. Validate for common issues (column drops, renames)\n\n## OUTPUT FORMAT\nUnified diff creating new migration file:\n\n```diff\ndiff --git a/migrations/0001_initial.py b/migrations/0001_initial.py\nnew file mode 100644\n--- /dev/null\n+++ b/migrations/0001_initial.py\n@@ -0,0 +1,20 @@\n+def upgrade():\n+    # Migration code\n+    pass\n+\n+def downgrade():\n+    # Rollback code\n+    pass\n```"
}
```

**Config:**
```json
{
  "roles": [
    {
      "id": "migration_generator",
      "file": "data_agents/migration_generator.json",
      "apply_diff": true
    }
  ]
}
```

**Usage:**
```bash
python multi_agent_codex.py \
  --config agent_families/data_main.json \
  --task "Create migration for User model: add email_verified field"
```

---

### Beispiel 2: Accessibility Auditor

**Use Case:** UI/UX Accessibility Review

**Rollen-Datei** (`agent_families/designer_agents/a11y_auditor.json`):
```json
{
  "id": "a11y_auditor",
  "name": "Accessibility Auditor",
  "role": "Accessibility Expert (WCAG 2.1 AA)",
  "prompt_template": "# ACCESSIBILITY AUDIT\n\n## TASK\n{task}\n\n## UI CODE\n{implementer_output}\n\n## DESIGN SPECS\n{ui_designer_output}\n\n## AUDIT CHECKLIST\nReview for WCAG 2.1 Level AA compliance:\n\n### Perceivable\n- [ ] Alt text for images\n- [ ] Color contrast ratios (4.5:1 for text)\n- [ ] No color-only information\n\n### Operable\n- [ ] Keyboard navigation\n- [ ] Focus indicators\n- [ ] No keyboard traps\n\n### Understandable\n- [ ] Clear labels\n- [ ] Error messages\n- [ ] Consistent navigation\n\n### Robust\n- [ ] Valid HTML\n- [ ] ARIA attributes\n- [ ] Screen reader support\n\n## OUTPUT FORMAT\n# Accessibility Audit Report\n\n## Pass ✅\n- [List passing criteria]\n\n## Fail ❌\n- [List failing criteria with severity]\n\n## Recommendations\n- [Specific fixes with code examples]\n\n## WCAG Compliance Score\n[X]% compliant"
}
```

---

### Beispiel 3: Performance Profiler

**Use Case:** Performance-Analyse und Optimierungs-Vorschläge

**Rollen-Datei** (`agent_families/developer_agents/performance_profiler.json`):
```json
{
  "id": "performance_profiler",
  "name": "Performance Profiler",
  "role": "Performance Engineering Expert",
  "prompt_template": "# PERFORMANCE ANALYSIS\n\n## TASK\n{task}\n\n## CODE\n{implementer_output}\n\n## ANALYSIS AREAS\n\n### 1. Time Complexity\n- Identify O(n²) or worse algorithms\n- Suggest optimizations\n\n### 2. Memory Usage\n- Large data structure allocations\n- Memory leaks (unclosed resources)\n- Unnecessary copies\n\n### 3. Database Queries\n- N+1 query problems\n- Missing indexes\n- Unoptimized joins\n\n### 4. Network I/O\n- Sequential API calls (can be parallelized?)\n- Large payloads\n- Missing caching\n\n### 5. CPU-Intensive Operations\n- Regex in loops\n- Unnecessary serialization\n- Blocking operations\n\n## OUTPUT FORMAT\n# Performance Analysis Report\n\n## Summary\n[Overall assessment]\n\n## Critical Issues (P0)\n### Issue: [Title]\n**Location:** [file:line]\n**Impact:** [e.g., \"100x slowdown on 10k items\"]\n**Fix:**\n```diff\n[proposed change]\n```\n\n## Medium Issues (P1)\n...\n\n## Optimizations (P2)\n...\n\n## Benchmarks\n[Expected improvements]"
}
```

---

### Beispiel 4: Dependency Updater

**Use Case:** Automatisches Update von Dependencies mit Breaking-Change-Detection

**Rollen-Datei** (`agent_families/devops_agents/dependency_updater.json`):
```json
{
  "id": "dependency_updater",
  "name": "Dependency Updater",
  "role": "DevOps Engineer specialized in dependency management",
  "prompt_template": "# DEPENDENCY UPDATE TASK\n\n## TASK\n{task}\n\n## CURRENT DEPENDENCIES\n{snapshot}\n\n## INSTRUCTIONS\n\n1. **Analyze** current dependency versions\n2. **Check** for available updates\n3. **Identify** breaking changes (major version bumps)\n4. **Update** dependency files (requirements.txt, package.json, etc.)\n5. **Document** changes and migration steps\n\n## SAFETY CHECKS\n- Pin transitive dependencies if major update\n- Check for security vulnerabilities\n- Note deprecated APIs\n\n## OUTPUT FORMAT\n\n### Part 1: Dependency Updates (as diff)\n```diff\ndiff --git a/requirements.txt b/requirements.txt\n--- a/requirements.txt\n+++ b/requirements.txt\n@@ -1,5 +1,5 @@\n-django==3.2.0\n+django==4.2.0\n```\n\n### Part 2: Migration Guide\n# Dependency Update Report\n\n## Updated\n- django: 3.2.0 → 4.2.0 (MAJOR)\n  - **Breaking Changes:**\n    - `django.conf.urls.url()` removed, use `path()` instead\n  - **Migration Steps:**\n    1. Replace `url()` with `re_path()` or `path()`\n    2. Update middleware settings\n\n## Security Fixes\n- [List CVEs fixed]\n\n## Testing Checklist\n- [ ] Run test suite\n- [ ] Check deprecated API usage\n- [ ] Verify third-party integrations"
}
```

---

## Troubleshooting

### Problem: Rolle generiert kein Output

**Symptom:**
```
implementer_1.md ist leer
```

**Mögliche Ursachen:**

1. **Timeout zu kurz**
   ```json
   {"timeout_sec": 600}  // Zu wenig für komplexe Tasks
   ```
   **Fix:** Erhöhe Timeout
   ```json
   {"timeout_sec": 3600}
   ```

2. **Prompt zu vage**
   ```json
   {"prompt_template": "{task}"}  // Keine Anweisungen
   ```
   **Fix:** Füge klare Instruktionen hinzu
   ```json
   {
     "prompt_template": "# TASK\n{task}\n\n# INSTRUCTIONS\n1. Analyze\n2. Implement\n3. Output as diff"
   }
   ```

3. **Fehlende Platzhalter**
   ```json
   {"prompt_template": "Use {architect_output}"}
   ```
   Aber `architect` existiert nicht in Pipeline.

   **Fix:** Prüfe `depends_on` Kette

---

### Problem: Diff wird nicht angewendet

**Symptom:**
```
No diffs found in implementer_1.md
```

**Ursache:** Output nicht im unified diff Format

**Fix:** Explizit Format fordern
```json
{
  "prompt_template": "...\n\n# OUTPUT FORMAT (CRITICAL)\nYou MUST output in unified diff format:\n\n```diff\ndiff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -10,3 +10,5 @@\n existing line\n+new line\n```\n\nDo NOT include explanations inside the diff block."
}
```

---

### Problem: Shard-Overlaps

**Symptom:**
```
Shard validation failed: Overlaps detected
```

**Ursache:** Mehrere Instanzen ändern dieselbe Datei

**Fix 1:** Klarere `allowed_paths` im Task
```markdown
# Feature A
## Allowed paths
- app/auth/jwt.py
- app/auth/tokens.py

# Feature B
## Allowed paths
- app/auth/rbac.py
- app/models/role.py
```

**Fix 2:** Overlap-Policy anpassen
```json
{
  "overlap_policy": "warn"  // Statt "forbid"
}
```

---

### Problem: Rolle ignoriert Context

**Symptom:** Implementer ignoriert Architect's Plan

**Ursache:** `{architect_output}` nicht im Prompt

**Fix:**
```json
{
  "prompt_template": "# TASK\n{task}\n\n# ARCHITECTURE PLAN (READ THIS FIRST)\n{architect_summary}\n\n# NOW IMPLEMENT\n..."
}
```

---

## Weitere Ressourcen

- 📖 [Konfiguration](CONFIGURATION.md) - Alle Config-Optionen
- 📖 [Sharding-Dokumentation](SHARDING.md) - Parallele Ausführung
- 📁 [Beispiel-Rollen](../agent_families/) - Vordefinierte Rollen
- 📚 [Hauptdokumentation](../README.md) - Zurück zur Übersicht
