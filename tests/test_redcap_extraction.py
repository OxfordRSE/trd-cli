import unittest
import json
from trd_cli.main import extract_redcap_ids


class RedcapExtraction(unittest.TestCase):
    def test_parse_records(self):
        with open("fixtures/redcap_export.json", "r") as f:
            records = json.load(f)
        self.assertEqual(
            {
                "one-oh-one": {
                    "gad7": [("2222222", 1)],
                    "mania": [],
                    "phq9": [("1111111", 1), ("121212", 1)],
                    "reqol10": [],
                    "study_id": "101",
                    "wsas": [],
                },
                "one-oh-two": {
                    "gad7": [("1231241", 1)],
                    "mania": [],
                    "phq9": [],
                    "reqol10": [],
                    "study_id": "102",
                    "wsas": [],
                },
            },
            extract_redcap_ids(records),
        )


if __name__ == "__main__":
    unittest.main()
