import unittest
from pathlib import Path
import sys
import os

# Add the repo root to sys.path so we can import from scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_atlas import (
    parse_commit,
    _is_ignored,
    _strip_dynamic_content,
    file_stats,
    find_entrypoints,
    IGNORE_NAMES
)

class TestGenerateAtlas(unittest.TestCase):
    
    def test_parse_commit(self):
        # Normal conventional commit
        hash1, cat1, msg1 = parse_commit("abcd123 feat: add new feature")
        self.assertEqual(hash1, "abcd123")
        self.assertEqual(cat1, "Features")
        self.assertEqual(msg1, "feat: add new feature")
        
        # Breaking change
        hash2, cat2, msg2 = parse_commit("efgh456 feat!: major breaking change")
        self.assertEqual(hash2, "efgh456")
        self.assertEqual(cat2, "Features")
        self.assertEqual(msg2, "feat!: major breaking change")
        
        # Scoped commit
        hash3, cat3, msg3 = parse_commit("ijkl789 fix(ui): fix button layout")
        self.assertEqual(hash3, "ijkl789")
        self.assertEqual(cat3, "Bug Fixes")
        self.assertEqual(msg3, "fix(ui): fix button layout")
        
        # Other commit
        hash4, cat4, msg4 = parse_commit("mnop012 Initial commit")
        self.assertEqual(hash4, "mnop012")
        self.assertEqual(cat4, "Other")
        self.assertEqual(msg4, "Initial commit")

    def test_is_ignored(self):
        # Ensure standard ignores work
        self.assertTrue(_is_ignored(REPO_ROOT / ".git" / "config"))
        self.assertTrue(_is_ignored(REPO_ROOT / "node_modules" / "test.js"))
        self.assertTrue(_is_ignored(REPO_ROOT / "src" / "__pycache__" / "file.pyc"))
        
        # Ensure valid paths are not ignored
        self.assertFalse(_is_ignored(REPO_ROOT / "scripts" / "generate_atlas.py"))
        self.assertFalse(_is_ignored(REPO_ROOT / "docs" / "atlas" / "repo-map.md"))

    def test_strip_dynamic_content(self):
        content = (
            "<!-- AUTO-GENERATED -->\n"
            "# Changelog\n"
            "*Generated: 2026-07-27*\n"
            "\n"
            "## Summary"
        )
        expected = (
            "<!-- AUTO-GENERATED -->\n"
            "# Changelog\n"
            "\n"
            "## Summary"
        )
        # Using _strip_dynamic_content to remove the generated line
        self.assertEqual(_strip_dynamic_content(content), expected)

    def test_file_stats(self):
        # We can't safely mock the entire file system easily without third-party tools,
        # but we can verify that file_stats returns a dict and doesn't crash on the repo itself.
        stats = file_stats()
        self.assertIsInstance(stats, dict)
        # At least .py extension should be present since we are in a Python repo
        self.assertIn(".py", stats)

    def test_find_entrypoints(self):
        # Ensure we can find some known entrypoints in this repo
        entrypoints = find_entrypoints()
        self.assertIsInstance(entrypoints, list)
        
        # We know scripts/generate_atlas.py is a python file, but it might not be a detected entrypoint
        # Let's just ensure the function returns successfully without crashing.
        self.assertTrue(all(isinstance(ep, tuple) for ep in entrypoints))
        self.assertTrue(all(len(ep) == 2 for ep in entrypoints))

if __name__ == "__main__":
    unittest.main()
