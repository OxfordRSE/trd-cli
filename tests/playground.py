import os
import unittest
from redcap import Project

from trd_cli.parse_tc import parse_tc


class PlaygroundTestCase(unittest.TestCase):
    REDCAP_TOKEN = None
    REDCAP_RESEARCHER_SECRET = None

    def setUp(self):
        with open("../.env.local", "r") as f:
            secrets = f.readlines()
            for line in secrets:
                s = line.split("=")
                if len(s) == 2:
                    key = s[0].strip()
                    value = s[1].strip().replace('"', "")
                    setattr(self, key, value)

        self.exports = {}
        for r, d, f in os.walk("../.."):
            for directory in list(filter(lambda x: x.startswith("tcexport"), d)):
                data = parse_tc(os.path.join(r, directory))
                self.exports[directory] = data

    def test_redcap_package(self):
        project = Project("https://redcaptest.medsci.ox.ac.uk/api/", self.REDCAP_TOKEN)
        records = project.export_records()
        self.assertGreater(len(records), 0)
        self.assertIn("nhsnumber", records[0])

    def test_redcap_package_researcher(self):
        project = Project(
            "https://redcaptest.medsci.ox.ac.uk/api/", self.REDCAP_RESEARCHER_SECRET
        )
        records = project.export_records()
        self.assertGreater(len(records), 0)
        self.assertNotIn("nhsnumber", records[0])

    def test_redcap_package_import(self):
        project = Project("https://redcaptest.medsci.ox.ac.uk/api/", self.REDCAP_TOKEN)
        data = [
            {
                "study_id": "102",
                "redcap_repeat_instrument": "phq9",
                "redcap_repeat_instance": 5,
                "phq9_1_interest_float": "3",
            },
        ]
        response = project.import_records(data)
        print(response)
        self.assertEqual(response.get("count"), 1)


if __name__ == "__main__":
    unittest.main()
