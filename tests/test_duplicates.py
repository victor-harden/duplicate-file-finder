import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import find_duplicates


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "a.txt").write_text("same content")
        (self.root / "b.txt").write_text("same content")
        (self.root / "c.txt").write_text("different")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "d.txt").write_text("same content")

    def tearDown(self):
        self.tmp.cleanup()

    def test_finds_group(self):
        groups = find_duplicates.find_duplicates([self.root])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["files"]), 3)

    def test_wasted_bytes(self):
        groups = find_duplicates.find_duplicates([self.root])
        self.assertEqual(groups[0]["wasted_bytes"], len("same content") * 2)

    def test_same_size_different_content(self):
        (self.root / "same-size.txt").write_text("same contenX")
        groups = find_duplicates.find_duplicates([self.root])
        self.assertEqual(len(groups), 1)

    def test_no_duplicates(self):
        other = self.root / "other"
        other.mkdir()
        (other / "x.txt").write_text("one")
        (other / "y.txt").write_text("two")
        self.assertEqual(find_duplicates.find_duplicates([other]), [])

    def test_delete_keeps_first(self):
        groups = find_duplicates.find_duplicates([self.root])
        removed = find_duplicates.delete_duplicates(groups)
        self.assertEqual(len(removed), 2)
        self.assertTrue((self.root / "a.txt").exists())

    def test_human(self):
        self.assertEqual(find_duplicates.human(999), "999 B")
        self.assertIn("KB", find_duplicates.human(1500))

    def test_cli_json(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = find_duplicates.main([str(self.root), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["duplicate_files"], 2)

    def test_cli_missing_path(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(find_duplicates.main([str(self.root / "nope")]), 2)


if __name__ == "__main__":
    unittest.main()
