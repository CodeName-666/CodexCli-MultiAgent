import unittest

from multi_agent.utils import format_prompt


class UtilsTest(unittest.TestCase):
    def test_format_prompt_missing_key(self) -> None:
        messages = {"error_prompt_missing_key": "missing {key} in {role_id}"}
        with self.assertRaises(ValueError):
            format_prompt("Hello {name}", {"task": "x"}, "role", messages)


if __name__ == "__main__":
    unittest.main()
