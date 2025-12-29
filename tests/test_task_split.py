import unittest

from multi_agent.task_split import (
    build_chunk_payload,
    build_chunks_from_plan,
    extract_headings,
    needs_split,
    split_task_markdown,
)


class TaskSplitTest(unittest.TestCase):
    def test_split_by_headings(self) -> None:
        text = "# Titel\n\nIntro\n\n## Modul A\nA1\n\n## Modul B\nB1\n"
        chunks = split_task_markdown(text, heading_level=2, min_chars=0, max_chars=10000)
        self.assertEqual(len(chunks), 3)
        self.assertIn("Modul A", chunks[1].content)
        self.assertIn("Modul B", chunks[2].content)

    def test_build_chunk_payload_with_carry(self) -> None:
        payload = build_chunk_payload("Basis", "Zusammenfassung", carry_over_max_chars=100)
        self.assertIn("Kontext aus vorherigem Run", payload)
        self.assertIn("Zusammenfassung", payload)

    def test_needs_split_by_heading_count(self) -> None:
        text = "# Titel\n\n## A\nx\n\n## B\ny\n\n## C\nz\n"
        cfg = {
            "heading_level": 2,
            "heuristic_max_headings": 2,
            "heuristic_max_chars": 0,
            "heuristic_max_tokens": 0,
        }
        self.assertTrue(needs_split(text, cfg))

    def test_build_chunks_from_plan(self) -> None:
        text = "# Titel\n\n## A\nA1\n\n## B\nB1\n\n## C\nC1\n"
        headings = extract_headings(text, 2)
        plan = [{"start": 1, "end": 2, "title": "A+B"}, {"start": 3, "end": 3, "title": "C"}]
        chunks = build_chunks_from_plan(text, headings, plan)
        self.assertEqual(len(chunks), 2)
        self.assertIn("## A", chunks[0].content)
        self.assertIn("## B", chunks[0].content)


if __name__ == "__main__":
    unittest.main()
