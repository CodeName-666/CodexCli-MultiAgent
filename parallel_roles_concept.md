# Parallel Role Instances Concept

## Ziel
Mehrere Instanzen derselben Rolle parallel starten, Aufgaben untereinander
koordiniert aufteilen, Konflikte vermeiden und Ergebnisse konsolidieren.

## Kernidee
Ein Orchestrator startet pro Rolle N Instanzen. Die Instanzen teilen sich ein
Task-Board (JSON) und einen Kommunikationskanal (append-only Log). Jede Instanz
claimt Teilaufgaben per Lock, kommuniziert Entscheidungen und liefert Artefakte,
die ein Integrator final zusammenfuehrt.

## Komponenten
- Orchestrator: startet Instanzen pro Rolle, verwaltet Laufstatus
- Task-Board: JSON-Datei fuer Aufgaben, Status, Claims, Abhaengigkeiten
- Claim/Lock: atomarer Claim pro Task (file-lock oder compare-and-swap)
- Kommunikationskanal: append-only Log fuer Abstimmung/Entscheidungen
- Output-Collector: sammelt Instanz-Artefakte
- Integrator: konsolidiert Ergebnisse und loest Konflikte

## Datenmodell (minimal)
- RoleInstance: { id, role_id, instance_id, status }
- Task: { id, title, status, claimed_by, deps }
- Message: { ts, sender, type, payload }
- Artifact: { role_id, instance_id, path }

## Konfiguration (Beispiel)
```json
{
  "roles": [
    { "id": "architect", "file": "roles/architect.json", "instances": 1 },
    { "id": "implementer", "file": "roles/implementer.json", "instances": 2 },
    { "id": "reviewer", "file": "roles/reviewer.json", "instances": 1 },
    { "id": "integrator", "file": "roles/integrator.json", "instances": 1 }
  ],
  "coordination": {
    "task_board": ".multi_agent_runs/<run_id>/task_board.json",
    "channel": ".multi_agent_runs/<run_id>/coordination.log",
    "lock_mode": "file_lock",
    "claim_timeout_sec": 300
  },
  "outputs": {
    "pattern": "<role>_<instance>.md"
  }
}
```

## Ablauf (Kurz)
1) Orchestrator erstellt Task-Board aus Gesamtaufgabe (Subtasks).
2) Pro Rolle werden N Instanzen parallel gestartet.
3) Instanzen lesen Task-Board, claimen Aufgaben und protokollieren im Log.
4) Instanzen koordinieren Aufteilung (z.B. "impl_1" nimmt API, "impl_2" nimmt UI).
5) Ergebnisse werden pro Instanz in getrennte Artefakte geschrieben.
6) Integrator sammelt Artefakte, loest Konflikte, erstellt finale Ausgabe.

## Claim/Lock-Mechanismus
- Task-Board wird als JSON mit Versionierung gespeichert.
- Claim erfolgt atomar: read -> check status == "open" -> write with updated claim.
- Bei Timeout kann ein Task re-claimed werden, wenn owner inaktiv ist.

## Kommunikationskanal
- Append-only Log mit JSON Lines (ts, sender, type, payload).
- Beispiel:
  {"ts":"2025-01-01T10:00:00Z","sender":"implementer#1","type":"claim","payload":{"task":"T1"}}
  {"ts":"2025-01-01T10:02:00Z","sender":"implementer#2","type":"decision","payload":{"note":"ich nehme T2"}}

## Output-Namensschema
- Instanz-spezifisch: implementer_1.md, implementer_2.md
- Integrator-Output: integrator.md

## Konfliktvermeidung
- Tasks so definieren, dass sie moeglichst disjunkt sind.
- Claim-Regeln verhindern Doppelarbeit.
- Integrator fuehrt Code- und Diff-Konflikte zusammen.

## Risiken
- Locking-Fehler: doppelte Claims bei parallelem Zugriff
- Diff-Konflikte bei ueberlappenden Aenderungen
- Livelock bei zu langer Abstimmung

## Annahmen
- Aufgaben sind sinnvoll in Subtasks teilbar.
- Rollen kooperieren und dokumentieren ihre Claims.

## Naechste Schritte
- Falls gewuenscht, kann ich konkrete Regeln fuer Konfliktaufloesung oder ein Protokoll fuer Abstimmungstypen im Log ausarbeiten.
