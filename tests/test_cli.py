from unittest import mock, TestCase, main
from click.testing import CliRunner
from click.core import Command
import os
import pandas
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
        self.pandas_read_csv_mock = self.enterContext(
            mock.patch("pandas.read_csv", autospec=True)
        )
        self.redcap_project_mock = self.enterContext(
            mock.patch("trd_cli.main.Project", autospec=True)
        )
        self.requests_post_mock = self.enterContext(
            mock.patch("requests.post", autospec=True)
        )

        # Set side effect for import_records method of the redcap Project mock
        def import_records_side_effect(records, *args, **kwargs):
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
        """Test email content correctness when there are new records, updates, and withdrawn consent."""
        self.subprocess_run_mock.return_value = 0
        self.pandas_read_csv_mock.return_value = pandas.DataFrame(
            {
                "record_id": [1, 2, 3],
                "consent_withdrawn": ["No", "No", "Yes"],
                "data_removal_request": ["No", "No", "Yes"],
                "column1": [1, 2, 3],
                "column2": [4, 5, 6],
                "column3": [7, 8, 9],
            }
        )

        # Mock REDCap data
        self.redcap_project_mock.return_value.export_records.return_value = {
            2: {
                "record_id": 2,
                "column1": 1,
                "column2": 1,
                "column3": 1,
                "consent_withdrawn": "No",
                "data_removal_request": "No",
            },
            3: {
                "record_id": 3,
                "column1": 3,
                "column2": 6,
                "column3": 9,
                "consent_withdrawn": "No",
                "data_removal_request": "No",
            },
        }

        runner = CliRunner()
        result = runner.invoke(cli)

        self.assertEqual(
            result.exit_code, 0, f"cli exit code {result.exit_code}:\n\n{result.output}"
        )
        self.requests_post_mock.assert_called_once()

        email_html = self.requests_post_mock.call_args[1]["data"]["html"]
        self.assertIn("Added New Records: 1", email_html)
        self.assertIn("Updated Records: 5", email_html)
        self.assertIn("Withdrawn Consent: 1 participants", email_html)
        self.assertIn("Data Deletion Requests: 1", email_html)
        self.assertIn("Withdrawn Consent IDs: 3", email_html)
        self.assertIn("Data Deletion Request IDs: 3", email_html)

    def test_email_sending_failure(self):
        """Test email sending failure scenario."""
        self.subprocess_run_mock.return_value = 0
        self.pandas_read_csv_mock.return_value = pandas.DataFrame(
            {
                "record_id": [1],
                "consent_withdrawn": ["No"],
                "data_removal_request": ["No"],
                "column1": [1],
                "column2": [4],
                "column3": [7],
            }
        )

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
