from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import agscope, docuscope


class AGScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_reads_french_ag_rule_keys_and_normalizes_accents(self) -> None:
        run = RunContext(self.instance, "agscope")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)

        agscope.analyze(self.instance, run)

        _, rows = read_csv(self.instance.register("ag"))
        convocation = next(row for row in rows if row["file_name"] == "2026-04-29_convocation_ag.txt")
        self.assertGreater(int(convocation["resolution_count"]), 0)
        self.assertGreater(int(convocation["annex_hits"]), 0)
        self.assertIn("article 24", convocation["majority_terms"])
        self.assertIn("article 25", convocation["majority_terms"])


if __name__ == "__main__":
    unittest.main()
