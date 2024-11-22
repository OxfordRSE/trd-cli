import json
import os

from redcap import Project
import click
import requests

from trd_cli.questionnaires import QUESTIONNAIRES, dump_redcap_structure
from trd_cli.main_functions import extract_redcap_ids, get_true_colours_data, compare_tc_to_rc

# Construct a logger that saves logged events to a dictionary that we can attach to an email later
import logging
from logging.config import dictConfig
from trd_cli.log_config import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)

LOGGER = logging.getLogger(__name__)


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
        tc_data = get_true_colours_data(
            true_colours_secret, true_colours_url, true_colours_username
        )
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
                *[f"{n}_record_id" for n in [q["code"] for q in QUESTIONNAIRES]],
            ]
        )
        redcap_data = extract_redcap_ids(redcap_records)
        click.echo(" - OK")

        # Compare the True Colours data to the REDCap data
        click.echo("Comparing True Colours data to REDCap data", nl=False)

        new_participants, new_responses = compare_tc_to_rc(
            tc_data=tc_data, redcap_id_data=redcap_data
        )
        new_participants_success_count = 0

        id_map = {}
        if len(new_participants) > 0:
            LOGGER.info(
                f"Added {len(new_participants)} new records: {', '.join(new_participants)}."
            )
            for p_id, data in new_participants.items():
                try:
                    new_id = redcap_project.generate_next_record_name()
                    id_map[p_id] = new_id
                    rc_response = redcap_project.import_records([
                        {"study_id": new_id, **data["private"]},
                        {"study_id": new_id, **data["info"]},
                    ])
                    assert rc_response["count"] == 2, f"Failed to import record for {p_id}."
                    new_participants_success_count += 1
                except Exception as e:
                    LOGGER.exception(e)

        if len(new_responses) > 0:
            patched_responses = []
            for r in new_responses:
                if isinstance(r["study_id"], str) and r["study_id"].startswith("__NEW__"):
                    p_id = r["study_id"][7:]
                    if p_id not in id_map:
                        LOGGER.error(f"{p_id} not in id_map for response {json.dumps(r)}")
                    else:
                        r["study_id"] = id_map[p_id]
                patched_responses.append(r)
            rc_response_r = redcap_project.import_records(patched_responses)
            if rc_response_r["count"] != len(new_responses):
                LOGGER.error(
                    (
                        f"Failed to import all new questionnaire responses. "
                        f"Tried {len(new_responses)}, succeeded with {rc_response_r.get('count')}"
                    )
                )
            else:
                LOGGER.info(
                    (
                        f"Added {len(new_responses)} new questionnaire responses: "
                        f"{', '.join([x[f'''{x['redcap_repeat_instrument']}_response_id'''] for x in new_responses])}."
                    )
                )

        click.echo(" - OK")
        click.echo(
            f"\t{len(new_participants)} new participants; {len(new_responses)} new responses."
        )

        # Scan logs and count errors and warnings
        log_file = "trd_cli.log"
        with open(log_file, "r") as f:
            log_data = f.read()
        error_count = log_data.count("ERROR")
        warning_count = log_data.count("WARNING")
        log_content = log_data.replace("\n", "<br />")

        # Send email summary
        click.echo("Sending email summary", nl=False)
        if new_participants_success_count != len(new_participants):
            added_participant_str = f"<strong>{new_participants_success_count}/{len(new_participants)}</strong>"
        else:
            added_participant_str = (
                f"{len(new_participants)}" if len(new_participants) > 0 else None
            )
        if len(new_responses) == 0:
            updated_record_str = None
        else:
            if rc_response_r["count"] != len(
                new_responses
            ):  # rc_response_r exists if new_responses > 0
                updated_record_str = (
                    f"<strong>{rc_response_r['count']}/{len(new_responses)}</strong>"
                )
            else:
                updated_record_str = f"{len(new_responses)}"

        if (
            not added_participant_str
            and not updated_record_str
            and error_count == 0
            and warning_count == 0
        ):
            click.echo(" - SKIPPED: No changes detected.")
            return

        if not added_participant_str and not updated_record_str:
            change_list = None
        else:
            change_list = f"""
<h2>Changes</h2>
    <ul>
        {f'< li > New Participants: {added_participant_str}</li>' if added_participant_str else ""}
        {f'< li > New Responses: {updated_record_str}</li>' if updated_record_str else ""}
    </ul>
</h2>
            """

        email_html = f"""
<html>
<body>
<h1>True Colours -> REDCap Data Comparison Summary</h1>
{change_list if change_list else ""}
<h2>Log Summary</h2>
    <details>
        <summary>Log File ({error_count} Errors, {warning_count} Warnings)</summary>
        <p>{log_content}</p>
    </details>
</h2>
</body>
</html>
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
        click.echo(f"{e.__class__.__name__}: {e}", err=True)
        exit(1)


# Allow dumping the REDCap structure to a given file
@click.command()
@click.option(
    "--output",
    "-o",
    default="redcap_structure.txt",
    help="Output file to dump the REDCap structure to.",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True)
)
def export_redcap_structure(output):
    """
    Export the required REDCap structure to a file so that REDCap can be correctly configured for the project.
    """
    dump_redcap_structure(output)


if __name__ == "__main__":
    cli()
