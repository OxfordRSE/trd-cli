import json
from typing import List
from unittest import mock, TestCase, main
from click.testing import CliRunner
from click.core import Command
import os
import requests

from trd_cli.questionnaires import QUESTIONNAIRES
from trd_cli.main import run, dump
from trd_cli.main_functions import compare_tc_to_rc

run: Command  # annotating to avoid linter warnings
dump: Command


class CliTest(TestCase):
    def setUp(self):
        # Setting up environment variables using enterContext to mock them for all tests
        env_vars = {
            "TRD_REDCAP_URL": "some_env_var_value",
            "TRD_REDCAP_TOKEN": "some_env_var_value",
            "TRD_TRUE_COLOURS_ARCHIVE": "fixtures/tc.zip",
            "TRD_MAILTO_ADDRESS": "some_env_var_value",
            "TRD_MAILGUN_SECRET": "some_env_var_value",
            "TRD_MAILGUN_DOMAIN": "some_env_var_value",
            "TRD_MAILGUN_USERNAME": "some_env_var_value",
            "TRD_LOG_DIR": ".test_logs",
            "TRD_LOG_LEVEL": "DEBUG",
        }
        self.enterContext(mock.patch.dict(os.environ, env_vars))

        # Setting up mocks for common modules used across tests
        self.subprocess_run_mock = self.enterContext(
            mock.patch("subprocess.run", autospec=True)
        )
        self.redcap_project_mock = self.enterContext(
            mock.patch("trd_cli.main.Project", autospec=True)
        )
        self.parse_tc_mock = self.enterContext(
            mock.patch("trd_cli.main_functions.parse_tc", autospec=True)
        )
        self.mock_compare_return = (
                    {'1255217154': {'info': {'info_birthyear_int': '1949', 'info_datetime': '2024-11-11T15:59:57.221799', 'info_is_test_bool': False, 'info_deceased_datetime': '', 'info_gender_int': '1', 'info_is_deceased_bool': ''}, 'private': {'birthdate': '1949-11-04', 'contactemail': 'b.tester@example.com', 'datetime': '2024-11-11T15:59:57.221799', 'firstname': 'Besty', 'id': '1255217154', 'lastname': 'Tester', 'mobilenumber': '+44 7000 000000', 'nhsnumber': '9910362813', 'preferredcontact': '0'}}, '1975714028': {'info': {'info_birthyear_int': '2018', 'info_datetime': '2024-11-11T15:59:57.221846', 'info_deceased_datetime': '', 'info_gender_int': '0', 'info_is_deceased_bool': ''}, 'private': {'birthdate': '2018-08-02', 'contactemail': 'jde-test1@avcosystems.com', 'datetime': '2024-11-11T15:59:57.221846', 'firstname': 'Jamie', 'id': '1975714028', 'lastname': 'Emery', 'mobilenumber': '', 'nhsnumber': '4389162012', 'preferredcontact': '0'}}},
                    [{'redcap_repeat_instance': 1, 'redcap_repeat_instrument': 'phq9', 'study_id': '__NEW__1255217154', "phq9_response_id": "123423"}]
                )
        self.compare_data_mock = self.enterContext(
            mock.patch(
                "trd_cli.main.compare_tc_to_rc",
                autospec=True,
                return_value=self.mock_compare_return
            )
        )
        self.requests_post_mock = self.enterContext(
            mock.patch("requests.post", autospec=True)
        )
        
        def load_tc_data_side_effect(*_args, **_kwargs):
            with open("fixtures/tc_data.json", "r") as f:
                return json.load(f)

        # Mocking the parse_tc function to return the data from fixtures/tc_data.json
        self.parse_tc_mock.side_effect = load_tc_data_side_effect
        
        def export_records_side_effect(*_args, **_kwargs):
            with open("fixtures/redcap_export.json", "r") as f:
                return json.load(f)

        # Mocking the export_records method to return the data from fixtures/redcap_export.json
        self.redcap_project_mock.return_value.export_records.side_effect = (
            export_records_side_effect
        )

        # Set side effect for import_records method of the redcap Project mock
        def import_records_side_effect(records, *_args, **_kwargs):
            return {"count": len(records)}

        # Mocking the import_records method to return {'count': len(records)}
        self.redcap_project_mock.return_value.import_records.side_effect = (
            import_records_side_effect
        )

    def test_redcap_api_failure(self):
        """Test REDCap API failure scenario."""
        self.redcap_project_mock.side_effect = Exception("REDCap API error")

        runner = CliRunner()
        result = runner.invoke(run)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Downloading data from REDCap - ERROR", result.output)

    def test_email_content(self):
        self.subprocess_run_mock.return_value = 0

        runner = CliRunner()
        result = runner.invoke(run)

        self.assertEqual(
            result.exit_code, 0, f"run exit code {result.exit_code}:\n\n{result.output}"
        )
        self.requests_post_mock.assert_called_once()

        email_html = self.requests_post_mock.call_args[1]["data"]["html"]
        self.assertIn("New Participants: 2", email_html)
        self.assertIn("New Responses: 1", email_html)
        self.assertIn("Log File (0 Errors, 0 Warnings)", email_html)
        self.assertIn(" INFO ", email_html)

    def test_email_sending_failure(self):
        """Test email sending failure scenario."""
        self.subprocess_run_mock.return_value = 0

        # Mock REDCap data
        self.redcap_project_mock.return_value.export_records.return_value = {}
        self.requests_post_mock.return_value.status_code = 500
        self.requests_post_mock.return_value.raise_for_status.side_effect = (
            requests.HTTPError()
        )

        runner = CliRunner()
        result = runner.invoke(run)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Sending email summary - ERROR", result.output)
    
    def test_double_upload(self):
        """
        - Parse a True Colours export versus a blank REDCap export.
        - Parse an updated True Colours export versus the previous REDCap export.
        """
        
        # We need to use the real compare for this to be a useful test
        self.compare_data_mock.side_effect = compare_tc_to_rc  

        def mock_next_record():
            i = 200  # the redcap_from_tc function below uses the 101-199 range for study_ids
            while True:
                i += 1
                yield str(i)
        self.redcap_project_mock.return_value.generate_next_record_name.side_effect = lambda: mock_next_record()
        
        def load_tc_data(f):
            with open(f, "r") as f:
                return json.load(f)
            
        def redcap_from_tc(tc_data: dict) -> List[dict]:
            out_data = []
            participant_id_map = {
                p["id"]: i + 101 for i, p in enumerate(tc_data["patient.csv"])
            }
            qq = [q["code"] for q in QUESTIONNAIRES]
            for qr in tc_data["questionnaireresponse.csv"]:
                if qr["responses"] is None:
                    continue
                q = [q["code"] for q in QUESTIONNAIRES if q["name"] == qr["interoperability"]["title"]][0]
                out = {
                    "study_id": participant_id_map[qr["patientid"]], 
                    "id": qr["patientid"],
                    "redcap_repeat_instrument": q, 
                    "redcap_repeat_instance": 1, 
                    **{f"{q}_response_id": "" for q in qq},
                    f"{q}_response_id": qr["id"]
                }
                out_data.append(out)
            return out_data

        initial_data = load_tc_data("fixtures/tc_data_initial.json")

        self.subTest("Initial upload")
        self.parse_tc_mock.side_effect = lambda _: initial_data 
        self.redcap_project_mock.return_value.export_records.side_effect = lambda *_, **_k: list()
        
        runner = CliRunner()
        result = runner.invoke(run)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("4 new participants; 3 new responses.", result.output)
        
        self.subTest("Second upload")
        self.parse_tc_mock.side_effect = lambda _: load_tc_data("fixtures/tc_data.json")
        self.redcap_project_mock.return_value.export_records.side_effect = lambda *_, **_k: redcap_from_tc(initial_data)

        runner = CliRunner()
        result = runner.invoke(run)
        
        self.assertEqual(result.exit_code, 0, result.output)

    def test_export_redcap_structure(self):
        """
        Test exporting the REDCap structure to a file
        """
        runner = CliRunner()
        result = runner.invoke(dump, "./.redcap_structure.txt")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(os.path.exists("./.redcap_structure.txt"))
    

if __name__ == "__main__":
    main()
