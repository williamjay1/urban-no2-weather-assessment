"""Small no-write regressions for the portable presentation layer."""
import copy
import unittest

from release_cli import PACKAGE, prepare_output
from verify_presentation_reproduction import AUDIT_RUNTIME, compare_ledger, normalize_vector


class PresentationChecks(unittest.TestCase):
    def test_generation_date_only(self):
        a = b"<svg><dc:date>2026-09-23</dc:date><text>3.158</text></svg>"
        b = a.replace(b"2026-09-23", b"2026-09-24")
        self.assertEqual(normalize_vector(a, ".svg")[0], normalize_vector(b, ".svg")[0])
        self.assertNotEqual(normalize_vector(a, ".svg")[0], normalize_vector(b.replace(b"3.158", b"4.158"), ".svg")[0])

    def test_missing_or_multiple_generation_dates_fail(self):
        for value in (b"no date", b"<dc:date>a</dc:date><dc:date>b</dc:date>"):
            with self.assertRaises(ValueError):
                normalize_vector(value, ".svg")

    def test_input_and_package_outputs_protected(self):
        for path in (PACKAGE, PACKAGE.parent, PACKAGE / "results/new", PACKAGE / "data/new", PACKAGE / "figures"):
            with self.assertRaises(ValueError):
                prepare_output(path, ["file.txt"])

    def test_ledger_runtime_not_science(self):
        audit = {key: 1 for key in AUDIT_RUNTIME}
        audit["models"] = 20
        second = dict(audit, elapsed_seconds=2)
        left = dict(input_audit=audit, tables={"T2": "3.16"}, main=[{"value": 3.158}])
        right = dict(input_audit=second, tables={"T2": "3.16"}, main=[{"value": 3.158}])
        self.assertEqual(len(compare_ledger(left, right, audit, second)), 1)
        changed = copy.deepcopy(right)
        changed["main"][0]["value"] = 4.158
        with self.assertRaises(ValueError):
            compare_ledger(left, changed, audit, second)


if __name__ == "__main__":
    unittest.main()
