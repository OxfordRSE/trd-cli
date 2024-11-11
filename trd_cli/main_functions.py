import subprocess
from typing import Tuple

from trd_cli.conversions import QUESTIONNAIRES, extract_participant_info, questionnaire_to_rc_record
from trd_cli.parse_tc import parse_tc

import logging
LOGGER = logging.getLogger(__name__)

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
    for record_id in ids:
        subset = list(filter(lambda x: x["id"] == record_id, records))
        if not all([s.get("study_id") == subset[0].get("study_id") for s in subset]):
            LOGGER.warning(
                (
                    f"Subset of {record_id} does not have the `study_id` field. Unique ids: "
                    f"{', '.join(set([s.get('study_id') for s in subset]))}."
                )
            )
        qr = {n: [] for n in [q["code"] for q in QUESTIONNAIRES]}
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
        out[record_id] = {"study_id": subset[0]["study_id"], **qr}
    return out


def get_true_colours_data(true_colours_secret, true_colours_url, true_colours_username):
    tc_dir = "tc_data"
    subprocess.run(
        f"scp {true_colours_username}@{true_colours_url} -i {true_colours_secret} dump.zip {tc_dir}/dump.zip",
        check=True,
    )
    # unzip the archive
    subprocess.run(f"unzip {tc_dir}/dump.zip", check=True)
    # We now have a directory of csv files (actually pipe-separated) we can load as a dict
    tc_data = parse_tc(tc_dir)
    return tc_data


def compare_tc_to_rc(redcap_data: dict, tc_data: dict) -> Tuple[dict, list]:
    """
    Compare the True Colours data to the REDCap data.
    
    :param redcap_data: parsed data exported from REDCap
    :param tc_data: parsed data exported from True Colours
    :return: a tuple of new_participants, new_responses
        new_participants is a dictionary of participant_id: {private, info} where private and info are dictionaries
        of data to be uploaded to REDCap. These need a new study_id generated by REDCap to be added before upload.
        new_responses is a list of dictionaries of data to be uploaded to REDCap
    """
    # First, search for patients who don't have REDCap entries
    new_participants = {}
    for p in tc_data["patient.csv"]:
        if p.get("id") not in redcap_data:
            private, info = extract_participant_info(p)
            new_participants[p.get("id")] = {
                "private": private,
                "info": info,
            }
    # Next, check for new questionnaire responses
    new_responses = []
    for qr in tc_data["questionnaireresponse.csv"]:
        pid = qr.get("patientid")
        qid = qr.get("id")
        interop = qr.get("interoperability")
        if interop is None:
            LOGGER.warning(
                f"Questionnaire response id={qid} missing interoperability field."
            )
            continue
        q_name = interop.get("title")
        q_code = list(filter(lambda q: q["name"] == q_name, QUESTIONNAIRES))[0]
        if q_code is None:
            LOGGER.warning(
                f"Questionnaire response id={qid} has unrecognised title {q_name}."
            )
            continue
        is_new = pid not in redcap_data[q_code] or qid not in [
            x[0] for x in redcap_data[q_code][pid]
        ]
        if is_new:
            if pid not in redcap_data[q_code]:
                instance_number = 1
            else:
                instance_number = max([x[1] for x in redcap_data[q_code][pid]]) + 1
            new_responses.append(
                {
                    "study_id": redcap_data[pid]["study_id"],
                    "redcap_repeat_instrument": q_code,
                    "redcap_repeat_instance": instance_number,
                    **questionnaire_to_rc_record(qr),
                }
            )
    return new_participants, new_responses