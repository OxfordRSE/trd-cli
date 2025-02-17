import json
from unittest import TestCase, main, mock

from trd_cli.main_functions import extract_redcap_ids, compare_tc_to_rc
from trd_cli.parse_tc import parse_tc


class RedcapExtractionTest(TestCase):
    def test_parse_records(self):
        with open("fixtures/redcap_export.json", "r") as f:
            records = json.load(f)
        self.assertEqual(
            {
                'one-oh-one': {
                    'aq10': [],
                    'asrs': [],
                    'audit': [],
                    'brss': [],
                    'consent': [],
                    'demo': [],
                    'dudit': [],
                    'gad7': [('2222222', 1)],
                    'info': [],
                    'mania': [],
                    'phq9': [('1111111', 1), ('121212', 1)],
                    'private': [('2024-11-04 12:59:24.973', 1)],
                    'pvss': [],
                    'reqol10': [],
                    'sapas': [],
                    'study_id': '101',
                    'wsas': []
                },
                'one-oh-two': {
                    'aq10': [],
                    'asrs': [],
                    'audit': [],
                    'brss': [],
                    'consent': [],
                    'demo': [],
                    'dudit': [],
                    'gad7': [('1231241', 1)],
                    'info': [],
                    'mania': [],
                    'phq9': [],
                    'private': [('2024-11-04 12:59:24.973', 1)],
                    'pvss': [],
                    'reqol10': [],
                    'sapas': [],
                    'study_id': '102',
                    'wsas': []
                }
            },
            extract_redcap_ids(records),
        )


class ParseTCTest(TestCase):
    def test_load_dir(self):
        tc_dir = "fixtures"
        parsed_tc = parse_tc(tc_dir)
        self.assertIn("patient.csv", parsed_tc)
        self.assertIn("questionnaireresponse.csv", parsed_tc)
        self.assertIsInstance(parsed_tc["patient.csv"], list)
        self.assertIsInstance(parsed_tc["questionnaireresponse.csv"], list)
        patient_fields = [
            "id", "nhsnumber", "gender"
        ]
        for f in patient_fields:
            with self.subTest(questionnaire="patient", field=f):
                self.assertIn(f, parsed_tc["patient.csv"][0])
        qr_fields = ["submitted", "interoperability", "scores"]
        for f in qr_fields:
            with self.subTest(questionnaire="questionnaireresponse", field=f):
                self.assertIn(f, parsed_tc["questionnaireresponse.csv"][0])


class CompareDataTest(TestCase):
    def setUp(self):
        with open("fixtures/redcap_export.json", "r") as f:
            rc_data = json.load(f)
            self.rc_data = extract_redcap_ids(rc_data)
        with open("fixtures/tc_data.json", "r") as f:
            self.tc_data = json.load(f)

        def questionnaire_to_rc_record_mock_side_effect(_data):
            return {}

        self.enterContext(mock.patch(
            "trd_cli.main_functions.questionnaire_to_rc_record",
            side_effect=questionnaire_to_rc_record_mock_side_effect
        ))

    def test_happy_path(self):
        tc_data = {
            "patient.csv": self.tc_data["patient.csv"][0:2],
            "questionnaireresponse.csv": self.tc_data["questionnaireresponse.csv"][0:1],
        }
        p, r = compare_tc_to_rc(tc_data, self.rc_data)
        self.assertEqual(len(p), 2)
        self.assertEqual(len(r), 5)
        for p_id in p:
            self.assertEqual(p_id, self.tc_data["patient.csv"][0]["id"])
            break
        self.assertTrue(r[0]["study_id"].startswith("__NEW__"))

    def test_just_patients(self):
        tc_data = {
            "patient.csv": self.tc_data["patient.csv"][0:2],
            "questionnaireresponse.csv": []
        }
        p, r = compare_tc_to_rc(tc_data, self.rc_data)
        self.assertEqual(len(p), 2)
        self.assertEqual(len(r), 4)

    def test_existing_patient(self):
        rc_data = {
            self.tc_data["patient.csv"][0]["id"]: {
                **self.rc_data["one-oh-one"]
            }
        }
        tc_data = {
            "patient.csv": self.tc_data["patient.csv"][0:1],
            "questionnaireresponse.csv": self.tc_data["questionnaireresponse.csv"][0:1],
        }
        p, r = compare_tc_to_rc(tc_data, rc_data)
        self.assertEqual(len(p), 0)
        self.assertEqual(len(r), 1)
        self.assertFalse(r[0]["study_id"].startswith("__NEW__"))

if __name__ == "__main__":
    main()
