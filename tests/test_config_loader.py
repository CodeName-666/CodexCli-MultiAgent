import json
import tempfile
import unittest
from pathlib import Path

from multi_agent.config_loader import load_role_config
from multi_agent.models import RoleDefaultsConfig


class ConfigLoaderTest(unittest.TestCase):
    def test_prompt_template_list_is_joined(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            role_path = base_dir / "role.json"
            role_path.write_text(
                json.dumps(
                    {
                        "id": "role_one",
                        "name": "Role One",
                        "role": "Tester",
                        "prompt_template": ["Line 1", "", "Line 2"],
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )

            role_cfg = load_role_config({"file": "role.json"}, base_dir, RoleDefaultsConfig({}))
            self.assertEqual(role_cfg.prompt_template, "Line 1\n\nLine 2")

    def test_prompt_template_list_requires_strings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            role_path = base_dir / "role.json"
            role_path.write_text(
                json.dumps(
                    {
                        "id": "role_two",
                        "name": "Role Two",
                        "role": "Tester",
                        "prompt_template": ["Line 1", 2],
                    },
                    ensure_ascii=True,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_role_config({"file": "role.json"}, base_dir, RoleDefaultsConfig({}))


if __name__ == "__main__":
    unittest.main()
