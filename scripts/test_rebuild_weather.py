"""Offline packaging guardrails; no writes or alteration of source files."""
import copy
import json
from pathlib import Path
import unittest

from rebuild_weather import PACKAGE, inside, output_target, validate_hourly


class WeatherInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((PACKAGE / "data/weather_hourly_utc/atlanta.json").read_text(encoding="utf-8"))

    def test_valid_frozen_hourly_source(self):
        self.assertEqual(len(validate_hourly(self.payload)), 61416)

    def test_non_utc_rejected(self):
        changed = dict(self.payload, utc_offset_seconds=-18000)
        with self.assertRaisesRegex(ValueError, "not UTC"):
            validate_hourly(changed)

    def test_wrong_unit_rejected(self):
        changed = copy.deepcopy(self.payload)
        changed["hourly_units"]["wind_speed_10m"] = "m/s"
        with self.assertRaisesRegex(ValueError, "units"):
            validate_hourly(changed)

    def test_missing_value_rejected(self):
        changed = copy.deepcopy(self.payload)
        changed["hourly"]["precipitation"][100] = None
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            validate_hourly(changed)

    def test_duplicate_hour_rejected(self):
        changed = copy.deepcopy(self.payload)
        changed["hourly"]["time"][100] = changed["hourly"]["time"][99]
        with self.assertRaisesRegex(ValueError, "incomplete, duplicated or unordered"):
            validate_hourly(changed)

    def test_missing_boundary_hour_rejected(self):
        changed = copy.deepcopy(self.payload)
        changed["hourly"] = {k: v[:-1] for k, v in changed["hourly"].items()}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            validate_hourly(changed)

    def test_manifest_paths_cannot_escape(self):
        for path in ("../outside.csv", "/outside.csv", "C:/outside.csv", "data\\outside.csv"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                inside(PACKAGE, path)

    def test_outputs_cannot_replace_package_inputs(self):
        for path in (PACKAGE, PACKAGE.parent, PACKAGE / "data", PACKAGE / "data/weather/new"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                output_target(PACKAGE, path)


if __name__ == "__main__":
    unittest.main()
