import os
import subprocess

from redcap import Project
import click
import requests

from trd_cli.conversions import extract_participant_info
from trd_cli.parse_tc import parse_tc

# Construct a logger that saves logged events to a dictionary that we can attach to an email later
import logging
from logging.config import dictConfig
from trd_cli.log_config import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)

LOGGER = logging.getLogger(__name__)

questionnaire_names = ["phq9", "gad7", "mania", "reqol10", "wsas"]


def extract_redcap_ids(records) -> dict:
    """
    Get a list of participants from REDCap.
    Each one will have a `study_id` (REDCap Id) and `id` our `patient.csv` `id` field.
    Each one will also have the `_response_id` for each questionnaire recorded in REDCap.

    Return a dictionary of `id`: with the `study_id` and the names of each questionnaire containing
    a list of tuples of (`_response_id`, `redcap_repeat_instance`) for all responses for that questionnaire.
    """
    ids = set([r.get("id") for r in records])
    out = {}
    for id in ids:
        subset = list(filter(lambda x: x["id"] == id, records))
        if not all([s.get("study_id") == subset[0].get("study_id") for s in subset]):
            LOGGER.warning(
                (
                    f"Subset of {id} does not have the `study_id` field. Unique ids: "
                    f"{', '.join(set([s.get('study_id') for s in subset]))}."
                )
            )
        qr = {n: [] for n in questionnaire_names}
        for s in subset:
            q_name = s.get("redcap_repeat_instrument")
            if q_name in qr.keys():
                if s.get(f"{q_name}_response_id") in list(
                    map(lambda x: x[0], qr[q_name])
                ):
                    if (
                        s.get("redcap_repeat_instance")
                        != qr[f"{q_name}_response_id"][1]
                    ):
                        LOGGER.warning(
                            (
                                f"{q_name}[{s.get(f'{q_name}_response_id')}] "
                                f"has instance {s.get('redcap_repeat_instance')}, "
                                f"but this id is already associated with instance {qr[f'{q_name}_response_id'][1]}."
                            )
                        )
                    continue
                qr[q_name].append(
                    (s.get(f"{q_name}_response_id"), s.get("redcap_repeat_instance"))
                )
            else:
                LOGGER.warning(
                    f"Unrecognised `redcap_repeat_instrument` value: {q_name}"
                )
        out[id] = {"study_id": subset[0]["study_id"], **qr}
    return out


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
        tc_data = parse_tc(tc_dir)
        click.echo(" - OK")

        # Download data from the REDCap API
        click.echo("Downloading data from REDCap", nl=False)
        redcap_project = Project(redcap_url, redcap_secret)
        redcap_records = redcap_project.export_records(
            fields=[
                "study_id",
                "id",
                "redcap_repeat_instrument",
                "redcap_repeat_instance",
                *[f"{n}_record_id" for n in questionnaire_names],
            ]
        )
        redcap_data = extract_redcap_ids(redcap_records)
        click.echo(" - OK")

        # Compare the True Colours data to the REDCap data
        click.echo("Comparing True Colours data to REDCap data", nl=False)

        # First, search for patients who don't have REDCap entries
        new_records = []
        for p in tc_data["patient.csv"]:
            if p.get("id") not in redcap_data:
                new_records.append(p.get("id"))
                # Get a new study_id from REDCap
                study_id = redcap_project.generate_next_record_name()
                # Upload private and info fields
                private, info = extract_participant_info(p)
                redcap_project.import_records([
                    {"study_id": study_id, **private},
                    {"study_id": study_id, **info},
                ])
        if len(new_records) > 0:
            LOGGER.info(f"Added {len(new_records)} new records: [{', '.join(new_records)}].")

        # Next, check for new questionnaire responses
        new_responses = []
        for qr in tc_data["questionnaireresponse.csv"]:
            id = qr.get("patientid")
            is_new = id not in redcap_data[q_name] or id not in [x[0] for x in redcap_data[q_name][id]]
            if id in redcap_data:


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

        # Scan logs and count errors and warnings
        log_file = "trd_cli.log"
        with open(log_file, "r") as f:
            log_data = f.read()
        error_count = log_data.count("ERROR")
        warning_count = log_data.count("WARNING")
        log_content = log_data.replace("\n", "<br />")

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
    <h2>Log Summary:</h2>
    <details>
        <summary>Log File ({error_count} Errors, {warning_count} Warnings)</summary>
        <p>{log_content}</p>
    </details>
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
        LOGGER.exception(e)
        raise e


if __name__ == "__main__":
    cli()
