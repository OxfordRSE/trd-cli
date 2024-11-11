import json
from unittest import mock, TestCase, main
from click.testing import CliRunner
from click.core import Command
import os
import subprocess
import requests

from trd_cli.main import cli

cli: Command  # annotating to avoid linter warnings


class CliTest(TestCase):
    def setUp(self):
        # Setting up environment variables using enterContext to mock them for all tests
        env_vars = {
            "REDCAP_SECRET": "some_env_var_value",
            "REDCAP_URL": "some_env_var_value",
            "TRUE_COLOURS_SECRET": "some_env_var_value",
            "TRUE_COLOURS_USERNAME": "some_env_var_value",
            "TRUE_COLOURS_URL": "some_env_var_value",
            "MAILGUN_DOMAIN": "some_env_var_value",
            "MAILGUN_USERNAME": "some_env_var_value",
            "MAILGUN_SECRET": "some_env_var_value",
            "MAILTO_ADDRESS": "some_env_var_value",
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
                    {'1255217154': {'info': {'info_birthyear_int': '1949', 'info_datetime': '2024-11-11T15:59:57.221799', 'info_deceased_datetime': '', 'info_gender_int': '1', 'info_is_deceased_bool': ''}, 'private': {'birthdate': '1949-11-04', 'contactemail': 'b.tester@example.com', 'datetime': '2024-11-11T15:59:57.221799', 'firstname': 'Besty', 'id': '1255217154', 'lastname': 'Tester', 'mobilenumber': '+44 7000 000000', 'nhsnumber': '9910362813', 'preferredcontact': '0'}}, '1975714028': {'info': {'info_birthyear_int': '2018', 'info_datetime': '2024-11-11T15:59:57.221846', 'info_deceased_datetime': '', 'info_gender_int': '0', 'info_is_deceased_bool': ''}, 'private': {'birthdate': '2018-08-02', 'contactemail': 'jde-test1@avcosystems.com', 'datetime': '2024-11-11T15:59:57.221846', 'firstname': 'Jamie', 'id': '1975714028', 'lastname': 'Emery', 'mobilenumber': '', 'nhsnumber': '4389162012', 'preferredcontact': '0'}}},
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

    def test_scp_download_failure(self):
        """Test SCP download failure scenario."""
        self.subprocess_run_mock.side_effect = subprocess.CalledProcessError(1, "scp")

        runner = CliRunner()
        result = runner.invoke(cli)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "Downloading True Colours dump from scp server - ERROR", result.output
        )

    def test_redcap_api_failure(self):
        """Test REDCap API failure scenario."""
        self.redcap_project_mock.side_effect = Exception("REDCap API error")

        runner = CliRunner()
        result = runner.invoke(cli)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Downloading data from REDCap - ERROR", result.output)

    def test_email_content(self):
        self.subprocess_run_mock.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli)

        self.assertEqual(
            result.exit_code, 0, f"cli exit code {result.exit_code}:\n\n{result.output}"
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
        result = runner.invoke(cli)

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Sending email summary - ERROR", result.output)


if __name__ == "__main__":
    main()
