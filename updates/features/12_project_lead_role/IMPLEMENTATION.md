# Implementation Plan: Project Lead Role

## Architektur

### Komponenten-Uebersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROJEKT-STRUKTUR                             │
├─────────────────────────────────────────────────────────────────────┤
│  multi_agent/                                                       │
│  ├─ project_lead/           ◄─── NEUES MODUL                       │
│  │   ├─ __init__.py                                                │
│  │   ├─ lead.py             # Hauptklasse ProjectLead              │
│  │   ├─ monitor.py          # TaskBoard/Output Monitoring          │
│  │   ├─ analyzer.py         # Fortschritts-Analyse                 │
│  │   ├─ intervention.py     # Intervention-Strategien              │
│  │   ├─ quality.py          # Qualitaets-Gates                     │
│  │   └─ reporter.py         # Status-Reporting                     │
│  │                                                                  │
│  ├─ pipeline.py             # Integration des Project Lead         │
│  ├─ models.py               # ProjectLeadConfig Dataclass          │
│  └─ config_loader.py        # Config Parsing                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Datenfluss

```
┌──────────────────────────────────────────────────────────────────────┐
│                          PIPELINE.RUN()                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   1. Pipeline Start                                                  │
│      │                                                               │
│      ├──► Start ProjectLead (parallel Task)                         │
│      │         │                                                     │
│      │         └──► MonitorLoop startet                             │
│      │                   │                                           │
│      │                   ▼                                           │
│   2. │    ┌─────────────────────────────────────────┐               │
│      │    │  PROJECT LEAD LOOP (async)              │               │
│      │    │  ┌───────────────────────────────────┐  │               │
│      │    │  │ 1. Read TaskBoard                 │  │               │
│      │    │  │ 2. Analyze Progress               │  │               │
│      │    │  │ 3. Check Quality Gates            │  │               │
│      │    │  │ 4. Decide Interventions           │  │               │
│      │    │  │ 5. Execute Interventions          │  │               │
│      │    │  │ 6. Update Status                  │  │               │
│      │    │  │ 7. Sleep(interval)                │  │               │
│      │    │  │ 8. Repeat until pipeline done     │  │               │
│      │    │  └───────────────────────────────────┘  │               │
│      │    └─────────────────────────────────────────┘               │
│      │                   │                                           │
│      │                   │ Interventions                             │
│      │                   ▼                                           │
│   3. ├──► Run Roles (parallel)  ◄────────────────────               │
│      │    ├─ Architect #1, #2                                        │
│      │    ├─ Implementer #1, #2, #3                                  │
│      │    └─ Tester #1, #2                                           │
│      │                                                               │
│   4. └──► Pipeline Complete                                          │
│            │                                                         │
│            └──► Stop ProjectLead, Final Report                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Implementation

### 1. Models (`multi_agent/models.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass(frozen=True)
class ProjectLeadMonitoringConfig:
    """Configuration for Project Lead monitoring behavior."""
    check_interval_sec: int = 30
    progress_estimation: bool = True
    output_validation: bool = True


@dataclass(frozen=True)
class ProjectLeadInterventionConfig:
    """Configuration for Project Lead intervention behavior."""
    enabled: bool = True
    threshold_progress_behind: float = 0.5  # Intervene if progress < 50% expected
    threshold_timeout_risk: float = 0.8     # Intervene if 80% of timeout elapsed
    max_reshards_per_role: int = 2
    cooldown_after_intervention_sec: int = 60


@dataclass(frozen=True)
class ProjectLeadQualityConfig:
    """Configuration for Project Lead quality checks."""
    check_sections: bool = True
    check_diff_syntax: bool = True
    check_overlap: bool = True
    reject_on_failure: bool = False


@dataclass(frozen=True)
class ProjectLeadReportingConfig:
    """Configuration for Project Lead reporting."""
    realtime_status: bool = True
    summary_on_completion: bool = True
    log_decisions: bool = True


@dataclass(frozen=True)
class ProjectLeadConfig:
    """Complete configuration for the Project Lead role."""
    enabled: bool = False
    cli_provider: str = "claude"
    model: str = "haiku"

    monitoring: ProjectLeadMonitoringConfig = field(
        default_factory=ProjectLeadMonitoringConfig
    )
    intervention: ProjectLeadInterventionConfig = field(
        default_factory=ProjectLeadInterventionConfig
    )
    quality: ProjectLeadQualityConfig = field(
        default_factory=ProjectLeadQualityConfig
    )
    reporting: ProjectLeadReportingConfig = field(
        default_factory=ProjectLeadReportingConfig
    )


@dataclass
class InstanceStatus:
    """Real-time status of an agent instance."""
    role_id: str
    instance_id: str
    shard_id: str | None
    status: str  # "pending", "running", "completed", "failed", "intervened"
    started_at: float | None
    elapsed_sec: float
    timeout_sec: float
    estimated_progress: float  # 0.0 to 1.0
    output_size: int
    validation_errors: List[str]
    intervention_count: int


@dataclass
class LeadDecision:
    """A decision made by the Project Lead."""
    timestamp: float
    decision_type: str  # "reshard", "extend_timeout", "feedback", "skip", "none"
    target_role: str
    target_instance: str
    reason: str
    details: Dict[str, Any]
    executed: bool = False
```

### 2. Project Lead Hauptklasse (`multi_agent/project_lead/lead.py`)

```python
"""Project Lead - Dynamic coordination role for multi-agent pipelines."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

from ..models import (
    ProjectLeadConfig,
    InstanceStatus,
    LeadDecision,
    RoleConfig,
)
from .monitor import TaskBoardMonitor
from .analyzer import ProgressAnalyzer
from .intervention import InterventionManager
from .quality import QualityGate
from .reporter import StatusReporter

if TYPE_CHECKING:
    from ..pipeline import PipelineRunContext

logger = logging.getLogger(__name__)


class ProjectLead:
    """
    Parallel coordination role that monitors and manages pipeline execution.

    The Project Lead runs alongside regular roles and can:
    - Monitor progress of all instances
    - Detect potential issues early
    - Trigger re-sharding when needed
    - Validate output quality
    - Make dynamic adjustments to execution
    """

    def __init__(
        self,
        config: ProjectLeadConfig,
        run_context: "PipelineRunContext",
    ):
        self.config = config
        self.run_context = run_context
        self.run_dir = run_context.run_dir

        # Components
        self.monitor = TaskBoardMonitor(run_context.task_board)
        self.analyzer = ProgressAnalyzer(config.monitoring)
        self.intervention_mgr = InterventionManager(
            config.intervention,
            run_context,
        )
        self.quality_gate = QualityGate(config.quality)
        self.reporter = StatusReporter(config.reporting, run_context.run_dir)

        # State
        self._running = False
        self._task: asyncio.Task | None = None
        self._decisions: List[LeadDecision] = []
        self._instance_statuses: Dict[str, InstanceStatus] = {}
        self._intervention_cooldowns: Dict[str, float] = {}

    async def start(self) -> None:
        """Start the Project Lead monitoring loop."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Project Lead started")

    async def stop(self) -> None:
        """Stop the Project Lead and generate final report."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Generate final report
        if self.config.reporting.summary_on_completion:
            await self.reporter.generate_final_report(
                self._decisions,
                self._instance_statuses,
            )

        logger.info("Project Lead stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        interval = self.config.monitoring.check_interval_sec

        while self._running:
            try:
                await self._check_cycle()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Project Lead error: {e}")
                await asyncio.sleep(interval)

    async def _check_cycle(self) -> None:
        """Single monitoring cycle."""
        # 1. Update instance statuses
        self._instance_statuses = await self.monitor.get_all_statuses()

        # 2. Analyze progress
        analysis = self.analyzer.analyze(self._instance_statuses)

        # 3. Check quality gates for completed outputs
        quality_issues = await self.quality_gate.check_outputs(
            self._instance_statuses,
            self.run_context,
        )

        # 4. Decide on interventions
        decisions = await self._make_decisions(analysis, quality_issues)

        # 5. Execute interventions
        for decision in decisions:
            if self._should_execute(decision):
                await self._execute_decision(decision)
                self._decisions.append(decision)

        # 6. Report status
        if self.config.reporting.realtime_status:
            await self.reporter.report_status(
                self._instance_statuses,
                analysis,
            )

    async def _make_decisions(
        self,
        analysis: Dict,
        quality_issues: List[Dict],
    ) -> List[LeadDecision]:
        """Make intervention decisions based on analysis."""
        decisions = []
        now = time.time()

        # Check for timeout risks
        for instance_id, status in self._instance_statuses.items():
            if status.status != "running":
                continue

            # Calculate timeout risk
            timeout_ratio = status.elapsed_sec / status.timeout_sec
            threshold = self.config.intervention.threshold_timeout_risk

            if timeout_ratio > threshold:
                # High timeout risk
                progress = status.estimated_progress

                if progress < 0.5:
                    # Low progress + high timeout = reshard
                    decisions.append(LeadDecision(
                        timestamp=now,
                        decision_type="reshard",
                        target_role=status.role_id,
                        target_instance=instance_id,
                        reason=f"Timeout risk ({timeout_ratio:.0%}) with low progress ({progress:.0%})",
                        details={
                            "elapsed": status.elapsed_sec,
                            "timeout": status.timeout_sec,
                            "progress": progress,
                        },
                    ))
                else:
                    # Good progress = extend timeout
                    decisions.append(LeadDecision(
                        timestamp=now,
                        decision_type="extend_timeout",
                        target_role=status.role_id,
                        target_instance=instance_id,
                        reason=f"Good progress ({progress:.0%}) near timeout",
                        details={
                            "new_timeout": int(status.timeout_sec * 1.5),
                        },
                    ))

        # Check for quality issues
        for issue in quality_issues:
            decisions.append(LeadDecision(
                timestamp=now,
                decision_type="feedback",
                target_role=issue["role_id"],
                target_instance=issue["instance_id"],
                reason=f"Quality issue: {issue['type']}",
                details=issue,
            ))

        return decisions

    def _should_execute(self, decision: LeadDecision) -> bool:
        """Check if a decision should be executed (cooldown, limits)."""
        instance_key = f"{decision.target_role}#{decision.target_instance}"
        now = time.time()

        # Check cooldown
        last_intervention = self._intervention_cooldowns.get(instance_key, 0)
        cooldown = self.config.intervention.cooldown_after_intervention_sec

        if now - last_intervention < cooldown:
            logger.debug(f"Skipping intervention for {instance_key}: cooldown active")
            return False

        # Check max interventions
        intervention_count = sum(
            1 for d in self._decisions
            if d.target_role == decision.target_role
            and d.decision_type == "reshard"
        )

        if intervention_count >= self.config.intervention.max_reshards_per_role:
            logger.debug(f"Skipping reshard for {decision.target_role}: max reached")
            return False

        return True

    async def _execute_decision(self, decision: LeadDecision) -> None:
        """Execute an intervention decision."""
        instance_key = f"{decision.target_role}#{decision.target_instance}"

        logger.info(
            f"Project Lead executing {decision.decision_type} "
            f"for {instance_key}: {decision.reason}"
        )

        try:
            if decision.decision_type == "reshard":
                await self.intervention_mgr.trigger_reshard(
                    decision.target_role,
                    decision.target_instance,
                    decision.details,
                )
            elif decision.decision_type == "extend_timeout":
                await self.intervention_mgr.extend_timeout(
                    decision.target_role,
                    decision.target_instance,
                    decision.details["new_timeout"],
                )
            elif decision.decision_type == "feedback":
                await self.intervention_mgr.inject_feedback(
                    decision.target_role,
                    decision.target_instance,
                    decision.details,
                )

            decision.executed = True
            self._intervention_cooldowns[instance_key] = time.time()

            if self.config.reporting.log_decisions:
                await self.reporter.log_decision(decision)

        except Exception as e:
            logger.error(f"Failed to execute decision: {e}")
            decision.executed = False
```

### 3. TaskBoard Monitor (`multi_agent/project_lead/monitor.py`)

```python
"""TaskBoard monitoring for Project Lead."""

from __future__ import annotations

import time
from typing import Dict, TYPE_CHECKING

from ..models import InstanceStatus

if TYPE_CHECKING:
    from ..coordination import TaskBoard


class TaskBoardMonitor:
    """Monitors TaskBoard for real-time instance status."""

    def __init__(self, task_board: "TaskBoard"):
        self.task_board = task_board
        self._start_times: Dict[str, float] = {}

    async def get_all_statuses(self) -> Dict[str, InstanceStatus]:
        """Get current status of all instances."""
        statuses = {}
        now = time.time()

        tasks = self.task_board.get_all_tasks()

        for task in tasks:
            task_id = task["id"]
            role_id = task_id.split("#")[0] if "#" in task_id else task_id

            # Track start time
            if task["status"] == "in_progress" and task_id not in self._start_times:
                self._start_times[task_id] = now

            started_at = self._start_times.get(task_id)
            elapsed = now - started_at if started_at else 0

            # Estimate progress (heuristic based on output size and time)
            output_size = task.get("output_size", 0)
            timeout = task.get("timeout_sec", 1800)
            estimated_progress = self._estimate_progress(elapsed, timeout, output_size)

            statuses[task_id] = InstanceStatus(
                role_id=role_id,
                instance_id=task_id,
                shard_id=task.get("shard_id"),
                status=task["status"],
                started_at=started_at,
                elapsed_sec=elapsed,
                timeout_sec=timeout,
                estimated_progress=estimated_progress,
                output_size=output_size,
                validation_errors=task.get("validation_errors", []),
                intervention_count=task.get("intervention_count", 0),
            )

        return statuses

    def _estimate_progress(
        self,
        elapsed: float,
        timeout: float,
        output_size: int,
    ) -> float:
        """
        Estimate progress based on heuristics.

        This is a simple heuristic that could be improved with ML.
        """
        # Time-based component (assume linear)
        time_progress = min(elapsed / timeout, 1.0) if timeout > 0 else 0

        # Output-based component (assume ~10KB typical output)
        expected_output = 10000
        output_progress = min(output_size / expected_output, 1.0)

        # Weighted combination
        return 0.4 * time_progress + 0.6 * output_progress
```

### 4. Progress Analyzer (`multi_agent/project_lead/analyzer.py`)

```python
"""Progress analysis for Project Lead."""

from __future__ import annotations

from typing import Dict, List
from ..models import InstanceStatus, ProjectLeadMonitoringConfig


class ProgressAnalyzer:
    """Analyzes instance progress and identifies issues."""

    def __init__(self, config: ProjectLeadMonitoringConfig):
        self.config = config

    def analyze(self, statuses: Dict[str, InstanceStatus]) -> Dict:
        """
        Analyze all instance statuses and return insights.

        Returns:
            Dict with analysis results including:
            - at_risk: instances at risk of timeout
            - blocked: instances that appear stuck
            - completed: successfully completed instances
            - average_progress: overall pipeline progress
        """
        at_risk = []
        blocked = []
        completed = []
        running = []

        for instance_id, status in statuses.items():
            if status.status == "completed":
                completed.append(instance_id)
            elif status.status == "running":
                running.append(instance_id)

                # Check timeout risk
                time_ratio = status.elapsed_sec / status.timeout_sec
                if time_ratio > 0.8:
                    at_risk.append({
                        "instance_id": instance_id,
                        "time_ratio": time_ratio,
                        "progress": status.estimated_progress,
                    })

                # Check if blocked (no progress for extended time)
                if time_ratio > 0.3 and status.estimated_progress < 0.1:
                    blocked.append({
                        "instance_id": instance_id,
                        "elapsed": status.elapsed_sec,
                        "progress": status.estimated_progress,
                    })

        # Calculate overall progress
        total_instances = len(statuses)
        if total_instances > 0:
            completed_ratio = len(completed) / total_instances
            running_progress = sum(
                statuses[i].estimated_progress for i in running
            ) / max(len(running), 1)
            average_progress = completed_ratio + (1 - completed_ratio) * running_progress * 0.5
        else:
            average_progress = 0

        return {
            "at_risk": at_risk,
            "blocked": blocked,
            "completed": completed,
            "running": running,
            "average_progress": average_progress,
            "total_instances": total_instances,
        }
```

### 5. Intervention Manager (`multi_agent/project_lead/intervention.py`)

```python
"""Intervention execution for Project Lead."""

from __future__ import annotations

import logging
from typing import Dict, Any, TYPE_CHECKING

from ..models import ProjectLeadInterventionConfig
from ..sharding import create_shard_plan

if TYPE_CHECKING:
    from ..pipeline import PipelineRunContext

logger = logging.getLogger(__name__)


class InterventionManager:
    """Manages and executes Project Lead interventions."""

    def __init__(
        self,
        config: ProjectLeadInterventionConfig,
        run_context: "PipelineRunContext",
    ):
        self.config = config
        self.run_context = run_context

    async def trigger_reshard(
        self,
        role_id: str,
        instance_id: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Trigger re-sharding for a struggling instance.

        This will:
        1. Cancel the current instance execution
        2. Split its shard into smaller sub-shards
        3. Distribute to available instances
        """
        logger.info(f"Triggering reshard for {role_id}#{instance_id}")

        # Get the role config
        role_cfg = self._get_role_config(role_id)
        if not role_cfg:
            logger.error(f"Role config not found: {role_id}")
            return

        # Get the current shard
        current_shard = self._get_current_shard(role_id, instance_id)
        if not current_shard:
            logger.error(f"Current shard not found for {instance_id}")
            return

        # Create new sub-shards using LLM sharding
        # Split remaining work into 2 smaller shards
        new_plan = create_shard_plan(
            role_cfg._replace(
                instances=2,
                shard_mode="llm",
            ),
            current_shard.content,
        )

        if new_plan and len(new_plan.shards) > 1:
            # Queue new shards for execution
            await self._queue_shards(role_id, new_plan.shards)

            # Mark original instance as "resharded"
            await self._mark_resharded(instance_id)
        else:
            logger.warning(f"Could not create sub-shards for {instance_id}")

    async def extend_timeout(
        self,
        role_id: str,
        instance_id: str,
        new_timeout: int,
    ) -> None:
        """Extend the timeout for an instance."""
        logger.info(f"Extending timeout for {instance_id} to {new_timeout}s")

        # Update TaskBoard with new timeout
        self.run_context.task_board.update_task(
            instance_id,
            {"timeout_sec": new_timeout},
        )

    async def inject_feedback(
        self,
        role_id: str,
        instance_id: str,
        feedback: Dict[str, Any],
    ) -> None:
        """
        Inject feedback into a running instance.

        Note: This requires the agent execution to support feedback injection,
        which may not be possible with all CLI providers.
        """
        logger.info(f"Injecting feedback for {instance_id}: {feedback.get('type')}")

        # Log feedback for post-run analysis
        # Direct injection during execution is complex and provider-dependent
        self.run_context.coordination_log.append({
            "type": "lead_feedback",
            "instance_id": instance_id,
            "feedback": feedback,
        })

    def _get_role_config(self, role_id: str):
        """Get role configuration by ID."""
        for role in self.run_context.cfg.roles:
            if role.id == role_id:
                return role
        return None

    def _get_current_shard(self, role_id: str, instance_id: str):
        """Get the current shard being processed."""
        shard_plan = self.run_context.shard_plans.get(role_id)
        if not shard_plan:
            return None

        # Find shard for this instance
        instance_num = int(instance_id.split("#")[1]) if "#" in instance_id else 1
        if instance_num <= len(shard_plan.shards):
            return shard_plan.shards[instance_num - 1]
        return None

    async def _queue_shards(self, role_id: str, shards) -> None:
        """Queue new shards for execution."""
        for shard in shards:
            self.run_context.task_board.add_task({
                "id": f"{role_id}#reshard-{shard.id}",
                "status": "pending",
                "shard": shard,
                "is_reshard": True,
            })

    async def _mark_resharded(self, instance_id: str) -> None:
        """Mark an instance as resharded (cancelled, replaced)."""
        self.run_context.task_board.update_task(
            instance_id,
            {"status": "resharded"},
        )
```

### 6. Quality Gate (`multi_agent/project_lead/quality.py`)

```python
"""Quality validation for Project Lead."""

from __future__ import annotations

import re
from typing import Dict, List, TYPE_CHECKING

from ..models import InstanceStatus, ProjectLeadQualityConfig

if TYPE_CHECKING:
    from ..pipeline import PipelineRunContext


class QualityGate:
    """Validates output quality for completed instances."""

    def __init__(self, config: ProjectLeadQualityConfig):
        self.config = config

    async def check_outputs(
        self,
        statuses: Dict[str, InstanceStatus],
        run_context: "PipelineRunContext",
    ) -> List[Dict]:
        """
        Check outputs for quality issues.

        Returns:
            List of quality issues found
        """
        issues = []

        for instance_id, status in statuses.items():
            if status.status != "completed":
                continue

            # Get output for this instance
            output = self._get_output(instance_id, run_context)
            if not output:
                continue

            role_cfg = self._get_role_config(status.role_id, run_context)
            if not role_cfg:
                continue

            # Check expected sections
            if self.config.check_sections and role_cfg.expected_sections:
                missing = self._check_sections(output, role_cfg.expected_sections)
                if missing:
                    issues.append({
                        "type": "missing_sections",
                        "role_id": status.role_id,
                        "instance_id": instance_id,
                        "missing": missing,
                    })

            # Check diff syntax
            if self.config.check_diff_syntax and role_cfg.apply_diff:
                diff_errors = self._check_diff_syntax(output)
                if diff_errors:
                    issues.append({
                        "type": "invalid_diff",
                        "role_id": status.role_id,
                        "instance_id": instance_id,
                        "errors": diff_errors,
                    })

            # Check for overlaps with other instances
            if self.config.check_overlap:
                overlaps = await self._check_overlaps(
                    instance_id, output, statuses, run_context
                )
                if overlaps:
                    issues.append({
                        "type": "file_overlap",
                        "role_id": status.role_id,
                        "instance_id": instance_id,
                        "overlapping_files": overlaps,
                    })

        return issues

    def _check_sections(
        self,
        output: str,
        expected_sections: List[str],
    ) -> List[str]:
        """Check if all expected sections are present."""
        missing = []
        for section in expected_sections:
            if section not in output:
                missing.append(section)
        return missing

    def _check_diff_syntax(self, output: str) -> List[str]:
        """Check diff syntax validity."""
        errors = []

        # Check for diff markers
        if "```diff" in output:
            diff_blocks = re.findall(r"```diff\n(.*?)```", output, re.DOTALL)
            for block in diff_blocks:
                # Basic validation
                if not any(line.startswith(("+", "-", " ", "@@")) for line in block.split("\n")):
                    errors.append("Diff block missing valid diff lines")

        return errors

    async def _check_overlaps(
        self,
        instance_id: str,
        output: str,
        statuses: Dict[str, InstanceStatus],
        run_context: "PipelineRunContext",
    ) -> List[str]:
        """Check for file overlaps with other instances."""
        # Extract files from this output
        my_files = self._extract_files_from_output(output)

        overlaps = []
        for other_id, other_status in statuses.items():
            if other_id == instance_id:
                continue
            if other_status.role_id != statuses[instance_id].role_id:
                continue
            if other_status.status != "completed":
                continue

            other_output = self._get_output(other_id, run_context)
            if not other_output:
                continue

            other_files = self._extract_files_from_output(other_output)

            # Find intersection
            common_files = my_files & other_files
            if common_files:
                overlaps.extend(common_files)

        return list(set(overlaps))

    def _extract_files_from_output(self, output: str) -> set:
        """Extract file paths mentioned in output."""
        files = set()

        # Match diff headers
        diff_pattern = re.compile(r"diff --git a/(.*?) b/")
        for match in diff_pattern.finditer(output):
            files.add(match.group(1))

        # Match --- and +++ lines
        file_pattern = re.compile(r"^[+-]{3} [ab]/(.*?)$", re.MULTILINE)
        for match in file_pattern.finditer(output):
            files.add(match.group(1))

        return files

    def _get_output(self, instance_id: str, run_context) -> str | None:
        """Get output for an instance."""
        role_id = instance_id.split("#")[0]
        results = run_context.results.get(role_id, [])
        for result in results:
            if result.agent.name == instance_id:
                return result.stdout
        return None

    def _get_role_config(self, role_id: str, run_context):
        """Get role config by ID."""
        for role in run_context.cfg.roles:
            if role.id == role_id:
                return role
        return None
```

### 7. Status Reporter (`multi_agent/project_lead/reporter.py`)

```python
"""Status reporting for Project Lead."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from ..models import (
    InstanceStatus,
    LeadDecision,
    ProjectLeadReportingConfig,
)
from ..utils import now_stamp


class StatusReporter:
    """Reports Project Lead status and decisions."""

    def __init__(self, config: ProjectLeadReportingConfig, run_dir: Path):
        self.config = config
        self.run_dir = run_dir
        self.log_file = run_dir / "project_lead.log"
        self.decisions_file = run_dir / "lead_decisions.json"

    async def report_status(
        self,
        statuses: Dict[str, InstanceStatus],
        analysis: Dict,
    ) -> None:
        """Report current pipeline status."""
        if not self.config.realtime_status:
            return

        # Build status summary
        running = len([s for s in statuses.values() if s.status == "running"])
        completed = len([s for s in statuses.values() if s.status == "completed"])
        total = len(statuses)
        progress = analysis.get("average_progress", 0)

        status_line = (
            f"[Project Lead] "
            f"Progress: {progress:.0%} | "
            f"Running: {running}/{total} | "
            f"Completed: {completed}/{total}"
        )

        if analysis.get("at_risk"):
            status_line += f" | At Risk: {len(analysis['at_risk'])}"

        print(status_line)

    async def log_decision(self, decision: LeadDecision) -> None:
        """Log a decision to file."""
        if not self.config.log_decisions:
            return

        log_entry = {
            "timestamp": now_stamp(),
            "type": decision.decision_type,
            "target": f"{decision.target_role}#{decision.target_instance}",
            "reason": decision.reason,
            "executed": decision.executed,
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def generate_final_report(
        self,
        decisions: List[LeadDecision],
        final_statuses: Dict[str, InstanceStatus],
    ) -> None:
        """Generate final summary report."""
        if not self.config.summary_on_completion:
            return

        report = {
            "generated_at": now_stamp(),
            "total_decisions": len(decisions),
            "decisions_by_type": {},
            "decisions_executed": sum(1 for d in decisions if d.executed),
            "final_statuses": {
                k: {
                    "status": v.status,
                    "progress": v.estimated_progress,
                    "interventions": v.intervention_count,
                }
                for k, v in final_statuses.items()
            },
        }

        # Count by type
        for d in decisions:
            dtype = d.decision_type
            report["decisions_by_type"][dtype] = report["decisions_by_type"].get(dtype, 0) + 1

        # Write report
        report_file = self.run_dir / "project_lead_report.json"
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Print summary
        print("\n" + "=" * 60)
        print("PROJECT LEAD SUMMARY")
        print("=" * 60)
        print(f"Total Decisions: {report['total_decisions']}")
        print(f"Executed: {report['decisions_executed']}")
        for dtype, count in report["decisions_by_type"].items():
            print(f"  - {dtype}: {count}")
        print("=" * 60 + "\n")
```

### 8. Pipeline Integration (`multi_agent/pipeline.py`)

```python
# Aenderungen an der bestehenden Pipeline-Klasse

class Pipeline:
    """Multi-agent pipeline orchestrator."""

    async def run(self, args, cfg) -> int:
        """Run the pipeline with optional Project Lead."""

        # Initialize Project Lead if enabled
        project_lead = None
        if cfg.project_lead and cfg.project_lead.enabled:
            from .project_lead import ProjectLead
            project_lead = ProjectLead(cfg.project_lead, self.run_context)
            await project_lead.start()

        try:
            # Existing pipeline logic
            result = await self._run_pipeline(args, cfg)
            return result

        finally:
            # Stop Project Lead
            if project_lead:
                await project_lead.stop()
```

## Implementation Steps

### Phase 1: Grundstruktur (Tag 1-2)
1. [ ] Models erstellen (ProjectLeadConfig, InstanceStatus, LeadDecision)
2. [ ] Modul-Struktur anlegen (project_lead/)
3. [ ] Config-Loader erweitern
4. [ ] Basis ProjectLead Klasse mit Start/Stop

### Phase 2: Monitoring (Tag 2-3)
1. [ ] TaskBoardMonitor implementieren
2. [ ] ProgressAnalyzer implementieren
3. [ ] StatusReporter implementieren
4. [ ] Integration in Monitor-Loop

### Phase 3: Intervention (Tag 3-5)
1. [ ] InterventionManager Grundstruktur
2. [ ] extend_timeout implementieren
3. [ ] trigger_reshard implementieren (nutzt LLM-Sharding)
4. [ ] inject_feedback implementieren
5. [ ] Cooldown und Limit-Logik

### Phase 4: Quality Gates (Tag 5-6)
1. [ ] QualityGate implementieren
2. [ ] Section-Check
3. [ ] Diff-Syntax-Check
4. [ ] Overlap-Detection

### Phase 5: Integration & Tests (Tag 6-7)
1. [ ] Pipeline Integration
2. [ ] Unit Tests fuer alle Komponenten
3. [ ] Integration Tests
4. [ ] Dokumentation

## Testplan

### Unit Tests

```python
# tests/test_project_lead.py

import pytest
from multi_agent.project_lead import ProjectLead
from multi_agent.models import ProjectLeadConfig, InstanceStatus


class TestProgressAnalyzer:
    def test_identifies_at_risk_instances(self):
        # Instance at 90% timeout with 30% progress
        statuses = {
            "impl#1": InstanceStatus(
                role_id="impl",
                instance_id="impl#1",
                status="running",
                elapsed_sec=900,
                timeout_sec=1000,
                estimated_progress=0.3,
                # ...
            )
        }
        analyzer = ProgressAnalyzer(ProjectLeadMonitoringConfig())
        result = analyzer.analyze(statuses)

        assert len(result["at_risk"]) == 1
        assert result["at_risk"][0]["instance_id"] == "impl#1"


class TestQualityGate:
    def test_detects_missing_sections(self):
        gate = QualityGate(ProjectLeadQualityConfig())
        output = "# Results\nSome content"
        expected = ["# Results", "# Tests", "# Summary"]

        missing = gate._check_sections(output, expected)

        assert "# Tests" in missing
        assert "# Summary" in missing
        assert "# Results" not in missing


class TestInterventionManager:
    def test_respects_cooldown(self):
        # Test that interventions respect cooldown period
        pass

    def test_respects_max_reshards(self):
        # Test that max_reshards_per_role is enforced
        pass
```

## Konfigurationsreferenz

### Vollstaendige Config-Optionen

```json
{
  "project_lead": {
    "enabled": true,
    "cli_provider": "claude",
    "model": "haiku",

    "monitoring": {
      "check_interval_sec": 30,
      "progress_estimation": true,
      "output_validation": true
    },

    "intervention": {
      "enabled": true,
      "threshold_progress_behind": 0.5,
      "threshold_timeout_risk": 0.8,
      "max_reshards_per_role": 2,
      "cooldown_after_intervention_sec": 60
    },

    "quality": {
      "check_sections": true,
      "check_diff_syntax": true,
      "check_overlap": true,
      "reject_on_failure": false
    },

    "reporting": {
      "realtime_status": true,
      "summary_on_completion": true,
      "log_decisions": true
    }
  }
}
```

## Abhaengigkeiten
- Feature 11: LLM-Sharding (fuer Re-Sharding)
- TaskBoard System
- CoordinationLog System
- asyncio fuer parallele Ausfuehrung

## Dokumentation
- [ ] PROJECT_LEAD.md Guide
- [ ] Beispiel-Configs
- [ ] Troubleshooting Guide
