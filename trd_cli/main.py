import datetime
import json
import os

from redcap import Project
import click
import requests

from trd_cli.questionnaires import QUESTIONNAIRES, dump_redcap_structure
from trd_cli.main_functions import extract_redcap_ids, get_true_colours_data, compare_tc_to_rc, \
    get_response_id_from_response_data

# Construct a logger that saves logged events to a dictionary that we can attach to an email later
import logging
from logging.config import dictConfig
from trd_cli.log_config import get_config

LOGGER = logging.getLogger(__name__)


@click.group()
@click.version_option()
@click.help_option()
def cli():
    pass


@cli.command()
@click.option(
    "--rc-url",
    help="The URL to connect to the REDCap API.",
    type=str,
    default=lambda: os.environ.get("TRD_REDCAP_URL"),
)
@click.option(
    "--rc-token",
    help="The secret to connect to the REDCap API.",
    type=str,
    default=lambda: os.environ.get("TRD_REDCAP_TOKEN"),
)
@click.option(
    "--tc-archive",
    help="The True Colours data archive .zip file.",
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    default=lambda: os.environ.get("TRD_TRUE_COLOURS_ARCHIVE"),
)
@click.option(
    "--mailto",
    help="The email address to send the summary to. If blank, no email will be sent.",
    type=str,
    default=lambda: os.environ.get("TRD_MAILTO_ADDRESS"),
)
@click.option(
    "--mg-secret",
    help="The secret for the Mailgun API.",
    type=str,
    default=lambda: os.environ.get("TRD_MAILGUN_SECRET"),
)
@click.option(
    "--mg-domain",
    help="The domain for the Mailgun API.",
    type=str,
    default=lambda: os.environ.get("TRD_MAILGUN_DOMAIN"),
)
@click.option(
    "--mg-username",
    help="The username for the Mailgun API.",
    type=str,
    default=lambda: os.environ.get("TRD_MAILGUN_USERNAME"),
)
@click.option(
    "--dry-run",
    help="Don't actually upload to REDCap.",
    is_flag=True,
    default=False,
)
@click.option(
    "--log-dir",
    help="The directory to save the log file to.",
    type=click.Path(file_okay=False, writable=True, resolve_path=True),
    default=lambda: os.environ.get("TRD_LOG_DIR", "/var/log/trd_cli"),
    show_default="/var/log/trd_cli",
)
@click.option(
    "--log-level",
    help="The log level to use.",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default=lambda: os.environ.get("TRD_LOG_LEVEL", "INFO"),
    show_default="INFO",
)
@click.help_option()
def run(
        rc_url,
        rc_token,
        tc_archive,
        mailto,
        mg_secret,
        mg_domain,
        mg_username,
        dry_run,
        log_dir,
        log_level,
):
    """
    Run the TRD CLI.

    Will connect to the TRD API and run the CLI.
    Running the CLI has several steps:
    1. Unpack the True Colours data.
    2. Download existing REDCap data.
    3. Compare the True Colours data to the REDCap data.
    4. Upload any new data to REDCap.
    5. Send an email summary of the changes. (optional)

    All arguments can be supplied as environment variables.
    """
    try:
        # Logfile has the date and time of the run
        log_file = os.path.join(log_dir, f"trd_cli-{datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log")
        dictConfig(get_config(log_file))
        LOGGER.setLevel(log_level)
        
        click.echo("Running TRD CLI")

        # Verify that all environment variables are set
        click.echo("Checking configuration", nl=False)
        required = {
            "rc_url": rc_url,
            "rc_token": rc_token,
            "tc_archive": tc_archive,
        }
        if mailto is not None:
            required = {
                **required,
                "mailto": mailto,
                "mg_secret": mg_secret,
                "mg_domain": mg_domain,
                "mg_username": mg_username,
            }
        for k, v in required.items():
            if v is None:
                raise ValueError(f"Missing required argument: {k}")
        click.echo(" - OK")

        # Connect to the True Colours scp server and download the zip dump
        click.echo("Unpacking True Colours archive", nl=False)
        tc_data = get_true_colours_data(tc_archive)
        click.echo(" - OK")

        # Download data from the REDCap API
        click.echo("Downloading data from REDCap", nl=False)
        redcap_project = Project(rc_url, rc_token)
        LOGGER.debug(f"Connected to REDCap project {redcap_project}")
        redcap_records = redcap_project.export_records(
            fields=[
                "study_id",
                "id",
                "updated",
                "info_updated_datetime",
                *[f"{n}_response_id" for n in [q["code"] for q in QUESTIONNAIRES]],
            ]
        )
        LOGGER.debug(f"Downloaded {len(redcap_records)} records from REDCap.")
        if len(redcap_records) > 0:
            LOGGER.debug(f"First record: {redcap_records[0]}")
        redcap_data = extract_redcap_ids(redcap_records)
        LOGGER.debug(f"Extracted REDCap records:\n {json.dumps(redcap_data, indent=4)}")
        click.echo(" - OK")

        # Compare the True Colours data to the REDCap data
        click.echo("Comparing True Colours data to REDCap data", nl=False)

        new_participants, new_responses = compare_tc_to_rc(
            tc_data=tc_data, redcap_id_data=redcap_data
        )
        LOGGER.debug(f"New participants:\n {json.dumps(new_participants, indent=4)}")
        LOGGER.debug(f"New responses:\n {len(new_responses)}")
        failed_pids = []
        failed_record_count = 0

        id_map = {}
        if len(new_participants) > 0:
            LOGGER.info(
                f"Generating record names for {len(new_participants)} new participants: {', '.join(new_participants)}."
            )
            for p_id in new_participants:
                try:
                    new_id = redcap_project.generate_next_record_name()
                    id_map[p_id] = new_id
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
            # Sort patched_responses by study_id so we obey REDCap's sequential ordering in the request
            patched_responses = sorted(patched_responses, key=lambda x: x["study_id"])
            LOGGER.debug(f"New responses:\n {json.dumps(patched_responses, indent=4)}")
            if not dry_run:
                rc_response_r = redcap_project.import_records(patched_responses)
                if rc_response_r["count"] != len(new_responses):
                    LOGGER.error(
                        (
                            f"Failed to import new questionnaire responses. "
                            f"Tried {len(new_responses)}, succeeded with {rc_response_r.get('count')}"
                        )
                    )
                    failed_record_count = len(new_responses) - rc_response_r["count"]
                else:
                    LOGGER.info(
                        (
                            f"Added {len(new_responses)} new questionnaire responses: "
                            f"{', '.join([get_response_id_from_response_data(x) for x in new_responses])}."
                        )
                    )

        click.echo(" - OK")
        click.echo(
            f"\t{len(new_participants)} new participants; {len(new_responses)} new responses."
        )
        if len(failed_pids) > 0:
            click.echo(f"\t{len(failed_pids)} participants failed to import: {failed_pids}.", err=True)
        if failed_record_count > 0:
            click.echo(f"\t{failed_record_count} responses failed to import.", err=True)

        # Scan logs and count errors and warnings
        with open(log_file, "r") as f:
            log_data = f.read()
        error_count = log_data.count("ERROR")
        warning_count = log_data.count("WARNING")
        log_content = log_data.replace("\n", "<br />")

        # Send email summary
        if mailto is not None:
            click.echo("Sending email summary", nl=False)
            if len(failed_pids) > 0:
                added_participant_str = f"<strong>{len(new_participants) - len(failed_pids)}/{len(new_participants)}</strong>"
            else:
                added_participant_str = (
                    f"{len(new_participants)}" if len(new_participants) > 0 else None
                )
            if len(new_responses) == 0:
                updated_record_str = None
            else:
                if failed_record_count > 0: 
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

            url = f"https://api.mailgun.net/v3/{mg_domain}/messages"
    
            data = {
                "from": f"TRD CLI <mailgun@{mg_domain}>",
                "to": mailto,
                "subject": f"TRD CLI Summary{' [DRY RUN]' if dry_run else ''}",
                "html": email_html,
            }
    
            headers = {"Content-Type": "multipart/form-data"}
    
            response = requests.post(
                url, data=data, headers=headers, auth=(mg_username, mg_secret)
            )
            response.raise_for_status()
            click.echo(" - OK")

    except Exception as e:
        click.echo(" - ERROR", err=True)
        LOGGER.exception(e)
        click.echo(f"{e.__class__.__name__}: {e}", err=True)
        exit(1)


# Allow dumping the REDCap structure to a given file
@cli.command()
@click.argument(
    "output",
    required=False,
    type=click.Path(dir_okay=False, writable=True, resolve_path=True)
)
@click.help_option()
def dump(output):
    """
    Export the required REDCap structure so that REDCap can be correctly configured for the project.
    
    An argument can be supplied to save the output to a file.
    """
    dump_redcap_structure(output)


if __name__ == "__main__":
    cli()
