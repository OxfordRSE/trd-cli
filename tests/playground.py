import csv
import os
import json
import unittest
from redcap import Project


class PlaygroundTestCase(unittest.TestCase):
    redcap_secret = None

    def setUp(self):
        with open("../secrets.tfvars", "r") as f:
            secrets = f.readlines()
            for line in secrets:
                s = line.split("=")
                if len(s) == 2:
                    key = s[0].strip()
                    value = s[1].strip().replace('"', "")
                    setattr(self, key, value)

        self.exports = {"_warnings": []}
        for r, d, f in os.walk("../.."):
            for directory in list(filter(lambda x: x.startswith("tcexport"), d)):
                self.exports[directory] = {}
                files = os.listdir(os.path.join(r, directory))
                for file in list(filter(lambda x: x.endswith(".csv"), files)):
                    with open(os.path.join(r, directory, file), "r") as h:
                        data = list(csv.DictReader(h, delimiter="|"))
                        if file == "questionnaireresponse.csv":
                            for i, row in enumerate(data):
                                for k, v in row.items():
                                    if k in ["responses", "scores", "interoperability"]:
                                        if v == "":
                                            row[k] = None
                                            continue
                                        try:
                                            row[k] = json.loads(v)
                                        except json.JSONDecodeError as e:
                                            self.exports["_warnings"].append(
                                                f"{directory}/{os.path.basename(file)}[{i}]:{k} - {e} [{v}]"
                                            )
                        self.exports[directory][os.path.basename(file)] = data

    def test_redcap_package(self):
        project = Project("https://redcaptest.medsci.ox.ac.uk/api/", self.redcap_secret)
        records = project.export_records()
        self.assertGreater(len(records), 0)

    def test_redcap_package_import(self):
        project = Project("https://redcaptest.medsci.ox.ac.uk/api/", self.redcap_secret)
        data = [
            {
                "study_id": "102",
                "redcap_repeat_instrument": "phq9",
                "redcap_repeat_instance": 5,
                "phq9_1_interest": "3",
            },
        ]
        response = project.import_records(data)
        print(response)
        self.assertEqual(response.get("count"), 1)


if __name__ == "__main__":
    unittest.main()
