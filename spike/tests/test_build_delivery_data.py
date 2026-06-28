import csv
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_delivery_data as build


class DeliveryCleaningTests(unittest.TestCase):
    def test_identifies_synthetic_sample_records(self):
        sample = {
            "id": "B00000",
            "name": "顺白切鸡饭店",
            "address": "番禺区某某路29号",
            "adname": "番禺区",
        }
        real = {
            "id": "B0FFJBB9PH",
            "name": "明洞妈妈参鸡汤(四季天地北座店)",
            "address": "赤岗北路118号四季天地北座F1层128-19",
            "adname": "海珠区",
        }

        self.assertTrue(build.is_synthetic_sample(sample))
        self.assertFalse(build.is_synthetic_sample(real))

    def test_filter_records_reports_removed_samples(self):
        records = [
            {"id": "B00000", "address": "番禺区某某路29号"},
            {"id": "B0FFJBB9PH", "address": "赤岗北路118号"},
        ]

        kept, removed = build.filter_synthetic_samples(records)

        self.assertEqual([r["id"] for r in kept], ["B0FFJBB9PH"])
        self.assertEqual([r["id"] for r in removed], ["B00000"])

    def test_writes_data_dictionary_for_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = build.write_data_dictionary(Path(tmp))

            with path.open(encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

        names = {row["field"] for row in rows}
        self.assertIn("label", names)
        self.assertIn("match_source", names)
        self.assertIn("signboard_pct", names)


if __name__ == "__main__":
    unittest.main()
