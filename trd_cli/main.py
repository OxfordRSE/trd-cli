import os
import subprocess
from redcap import Project
import click
import requests

from trd_cli.parse_tc import parse_tc


@click.command()
def cli():
    """
    Run the TRD CLI.

    Will connect to the TRD API and run the CLI.

    All arguments are taken from environment variables.
    These are:

    - `REDCAP_SECRET`: The secret to connect to the REDCap API.
    - `REDCAP_URL`: The URL to connect to the REDCap API.
    - `TRUE_COLOURS_SECRET`: The secret to connect to the True Colours `scp` server.
    - `TRUE_COLOURS_USERNAME`: The username to connect to the True Colours `scp` server.
    - `TRUE_COLOURS_URL`: The URL to connect to the True Colours `scp` server.
    """
    try:
        click.echo("Running TRD CLI")

        # Verify that all environment variables are set
        click.echo("Checking environment variables", nl=False)
        redcap_secret = os.environ["REDCAP_SECRET"]
        redcap_url = os.environ["REDCAP_URL"]
        true_colours_secret = os.environ["TRUE_COLOURS_SECRET"]
        true_colours_username = os.environ["TRUE_COLOURS_USERNAME"]
        true_colours_url = os.environ["TRUE_COLOURS_URL"]
        mailgun_domain = os.environ["MAILGUN_DOMAIN"]
        mailgun_username = os.environ["MAILGUN_USERNAME"]
        mailgun_secret = os.environ["MAILGUN_SECRET"]
        mailto_address = os.environ["MAILTO_ADDRESS"]
        click.echo(" - OK")

        # Connect to the True Colours scp server and download the zip dump
        click.echo("Downloading True Colours dump from scp server", nl=False)
        tc_dir = "tc_data"
        subprocess.run(
            f"scp {true_colours_username}@{true_colours_url} -i {true_colours_secret} dump.zip {tc_dir}/dump.zip",
            check=True,
        )
        # unzip the archive
        subprocess.run(f"unzip {tc_dir}/dump.zip", check=True)
        # We now have a directory of csv files (actually pipe-separated) we can load as a dict
        tc_data, tc_parse_warnings = parse_tc(tc_dir)
        click.echo(" - OK")

        # Download data from the REDCap API
        click.echo("Downloading data from REDCap", nl=False)
        redcap_project = Project(redcap_url, redcap_secret)
        redcap_data = redcap_project.export_records()
        click.echo(" - OK")

        # Compare the True Colours data to the REDCap data
        # If consent has been withdrawn and data removal is required, remove the data from the REDCap project
        # If consent has been withdrawn, alert the data manager via email
        # If there are new data, add to the REDCap project
        # If there are data discrepancies, alert the data manager via email
        click.echo("Comparing True Colours data to REDCap data", nl=False)
        new_records = []
        updated_records = []
        withdrawn_consent_ids = []
        data_deletion_request_ids = []
        for index, row in tc_data.iterrows():
            redcap_record = redcap_data.get(row["record_id"])
            if redcap_record is None:
                new_records.append(row)
            else:
                for field in row.keys():
                    # Check if consent has been withdrawn
                    if field == "consent_withdrawn" and row[field] == "Yes":
                        withdrawn_consent_ids.append(row["record_id"])
                        if row["data_removal_request"] == "Yes":
                            data_deletion_request_ids.append(row["record_id"])
                    if redcap_record[field] != row[field]:
                        updated_records.append(row)
        click.echo(" - OK")
        click.echo(
            f"\tRecords: {len(new_records)} new, {len(updated_records)} updated."
        )
        if len(withdrawn_consent_ids) > 0:
            click.echo(
                (
                    f"\tWithdrawn consent: {len(withdrawn_consent_ids)} participants, "
                    f"{len(data_deletion_request_ids)} request data deletion."
                )
            )

        # Update the REDCap project
        click.echo("Updating REDCap project", nl=False)
        added_record_request = redcap_project.import_records(new_records)
        updated_record_request = redcap_project.import_records(updated_records)
        click.echo(" - OK")

        # Send email summary
        click.echo("Sending email summary", nl=False)
        if added_record_request["count"] != len(new_records):
            added_record_str = (
                f"<strong>{added_record_request['count']}/{len(new_records)}</strong>"
            )
        else:
            added_record_str = f"{len(new_records)}" if len(new_records) > 0 else None
        if updated_record_request["count"] != len(updated_records):
            updated_record_str = f"<strong>{updated_record_request['count']}/{len(updated_records)}</strong>"
        else:
            updated_record_str = (
                f"{len(updated_records)}" if len(updated_records) > 0 else None
            )
        withdrawn_record_str = (
            f"{len(withdrawn_consent_ids)}" if len(withdrawn_consent_ids) > 0 else None
        )
        data_deletion_request_str = (
            f"{len(data_deletion_request_ids)}"
            if len(data_deletion_request_ids) > 0
            else None
        )

        if (
            not added_record_str
            and not updated_record_str
            and not withdrawn_record_str
            and not data_deletion_request_str
        ):
            click.echo(" - SKIPPED: No changes detected.")
            return

        if len(withdrawn_consent_ids):
            withdrawn_consent_ids_str = ", ".join(
                [str(x) for x in withdrawn_consent_ids]
            )
        else:
            withdrawn_consent_ids_str = ""

        if len(data_deletion_request_ids):
            data_deletion_ids_str = ", ".join(
                [str(x) for x in data_deletion_request_ids]
            )
        else:
            data_deletion_ids_str = "No data deletion requests."

        email_html = f"""
    <h1>True Colours -> REDCap Data Comparison Summary:</h1>
    <ul>
        {f'< li > Added New Records: {added_record_str}</li>' if added_record_str else ""}
        {f'< li > Updated Records: {updated_record_str}</li>' if updated_record_str else ""}
        {f'< li > Withdrawn Consent: {len(withdrawn_consent_ids)} participants</li>' if withdrawn_consent_ids else ""}
        {f'< li > Data Deletion Requests: {len(data_deletion_request_ids)}</li>' if data_deletion_request_ids else ""}
    </ul>
    {f'Withdrawn Consent IDs: {withdrawn_consent_ids_str}' if len(withdrawn_consent_ids) > 0 else ""}
    {f'Data Deletion Request IDs: {data_deletion_ids_str}' if len(withdrawn_consent_ids) > 0 else ""}
    """

        url = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        data = {
            "from": f"TRD CLI <mailgun@{mailgun_domain}>",
            "to": mailto_address,
            "subject": "TRD CLI Summary",
            "html": email_html,
        }

        headers = {"Content-Type": "multipart/form-data"}

        response = requests.post(
            url, data=data, headers=headers, auth=(mailgun_username, mailgun_secret)
        )
        response.raise_for_status()
        click.echo(" - OK")

    except Exception as e:
        click.echo(" - ERROR")
        raise e


if __name__ == "__main__":
    cli()
