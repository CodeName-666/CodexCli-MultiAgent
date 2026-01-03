#!/usr/bin/env python3
"""
Evaluation Runner für Multi-Agent vs. CLI Vergleich

Hilft beim systematischen Testen und Dokumentieren der Ergebnisse.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class EvaluationRunner:
    """Manages evaluation runs and result tracking."""

    def __init__(self, output_dir: Path = None):
        """Initialize the runner and ensure output directory exists."""
        self.output_dir = output_dir or Path("evaluation/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_test = None

    def start_test(self, task_name: str, approach: str) -> Dict:
        """
        Start a new test run.

        Args:
            task_name: Name of the task being tested
            approach: "multi_agent" or "direct_cli"

        Returns:
            Test session info
        """
        session = {
            "task_name": task_name,
            "approach": approach,
            "start_time": datetime.now().isoformat(),
            "start_timestamp": time.time(),
        }

        self.current_test = session

        print(f"\n{'='*60}")
        print(f"Starting Test: {task_name}")
        print(f"Approach: {approach}")
        print(f"Start Time: {session['start_time']}")
        print(f"{'='*60}\n")

        return session

    def end_test(self, notes: str = "") -> Dict:
        """
        End current test and calculate duration.

        Args:
            notes: Optional notes about the test run

        Returns:
            Completed test info
        """
        if not self.current_test:
            raise ValueError("No test currently running")

        end_time = time.time()
        duration = end_time - self.current_test["start_timestamp"]

        self.current_test["end_time"] = datetime.now().isoformat()
        self.current_test["duration_seconds"] = duration
        self.current_test["duration_minutes"] = duration / 60
        self.current_test["notes"] = notes

        print(f"\n{'='*60}")
        print(f"Test Complete: {self.current_test['task_name']}")
        print(f"Duration: {duration/60:.2f} minutes")
        print(f"{'='*60}\n")

        # Save result
        self._save_result(self.current_test)

        result = self.current_test
        self.current_test = None

        return result

    def record_metrics(
        self,
        code_quality: int,
        functionality: int,
        error_free: int,
        test_coverage: int,
        token_estimate: int = None,
        cost_estimate: float = None
    ) -> Dict:
        """
        Record quality metrics for current test.

        Args:
            code_quality: 1-5 rating
            functionality: 1-5 rating
            error_free: 1-5 rating
            test_coverage: 1-5 rating
            token_estimate: Estimated token usage
            cost_estimate: Estimated cost in USD

        Returns:
            Updated test info with metrics
        """
        if not self.current_test:
            raise ValueError("No test currently running")

        metrics = {
            "code_quality": code_quality,
            "functionality": functionality,
            "error_free": error_free,
            "test_coverage": test_coverage,
            "total_score": code_quality + functionality + error_free + test_coverage,
            "token_estimate": token_estimate,
            "cost_estimate": cost_estimate
        }

        self.current_test["metrics"] = metrics

        print("Metrics recorded:")
        print(f"  Code Quality: {code_quality}/5")
        print(f"  Functionality: {functionality}/5")
        print(f"  Error Free: {error_free}/5")
        print(f"  Test Coverage: {test_coverage}/5")
        print(f"  Total Score: {metrics['total_score']}/20")
        if token_estimate:
            print(f"  Tokens: ~{token_estimate:,}")
        if cost_estimate:
            print(f"  Cost: ${cost_estimate:.4f}")

        return self.current_test

    def _save_result(self, result: Dict):
        """Save result to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result['task_name']}_{result['approach']}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {filepath}")

    def compare_results(self, task_name: str):
        """
        Compare results for a specific task.

        Args:
            task_name: Name of the task to compare
        """
        # Find all results for this task
        results = []
        for filepath in self.output_dir.glob(f"{task_name}_*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                results.append(json.load(f))

        if not results:
            print(f"No results found for task: {task_name}")
            return

        # Group by approach
        by_approach = {}
        for result in results:
            approach = result['approach']
            if approach not in by_approach:
                by_approach[approach] = []
            by_approach[approach].append(result)

        # Print comparison
        print(f"\n{'='*60}")
        print(f"Comparison for Task: {task_name}")
        print(f"{'='*60}\n")

        for approach, approach_results in by_approach.items():
            print(f"\n{approach.upper()}:")
            print(f"  Runs: {len(approach_results)}")

            if approach_results and 'metrics' in approach_results[0]:
                # Calculate averages
                avg_score = sum(r['metrics']['total_score'] for r in approach_results) / len(approach_results)
                avg_time = sum(r['duration_minutes'] for r in approach_results) / len(approach_results)

                print(f"  Avg Score: {avg_score:.1f}/20")
                print(f"  Avg Time: {avg_time:.1f} minutes")

                if 'token_estimate' in approach_results[0]['metrics']:
                    avg_tokens = sum(r['metrics'].get('token_estimate', 0) for r in approach_results if r['metrics'].get('token_estimate')) / len([r for r in approach_results if r['metrics'].get('token_estimate')])
                    print(f"  Avg Tokens: ~{avg_tokens:,.0f}")


def interactive_mode():
    """
    Interactive evaluation session.

    Collects task metadata, manual ratings, and optional comparison queries.
    """
    runner = EvaluationRunner()

    print("\n=== Multi-Agent Evaluation Tool ===\n")

    # Get task info
    task_name = input("Task name (e.g., 'api_endpoint_creation'): ").strip()

    print("\nApproach:")
    print("  1. Multi-Agent")
    print("  2. Direct CLI")
    choice = input("Select (1/2): ").strip()
    approach = "multi_agent" if choice == "1" else "direct_cli"

    # Start test
    runner.start_test(task_name, approach)

    print("\n--- Perform your task now ---")
    print("Press ENTER when complete...")
    input()

    # Get metrics
    print("\n=== Rate the Results ===\n")

    code_quality = int(input("Code Quality (1-5): ").strip())
    functionality = int(input("Functionality (1-5): ").strip())
    error_free = int(input("Error Free (1-5): ").strip())
    test_coverage = int(input("Test Coverage (1-5): ").strip())

    token_str = input("Token estimate (optional, press ENTER to skip): ").strip()
    token_estimate = int(token_str) if token_str else None

    cost_str = input("Cost estimate in USD (optional, press ENTER to skip): ").strip()
    cost_estimate = float(cost_str) if cost_str else None

    # Record metrics
    runner.record_metrics(
        code_quality=code_quality,
        functionality=functionality,
        error_free=error_free,
        test_coverage=test_coverage,
        token_estimate=token_estimate,
        cost_estimate=cost_estimate
    )

    # Get notes
    notes = input("\nAdditional notes (optional): ").strip()

    # End test
    runner.end_test(notes=notes)

    # Ask if user wants to compare
    compare = input("\nCompare with other results for this task? (y/N): ").strip().lower()
    if compare == 'y':
        runner.compare_results(task_name)


def main():
    """CLI entry point for evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Evaluation runner for Multi-Agent vs CLI comparison"
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )

    parser.add_argument(
        "--compare",
        "-c",
        help="Compare results for a specific task"
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.compare:
        runner = EvaluationRunner()
        runner.compare_results(args.compare)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
