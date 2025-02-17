import os
import subprocess
from typing import Tuple, List, Optional

from redcap import Project

from trd_cli.conversions import extract_participant_info
from trd_cli.questionnaires import (
    QUESTIONNAIRES,
    questionnaire_to_rc_record,
    get_redcap_structure,
    get_questionnaire_by_name
)
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
                # private and info are not filled by QUESTIONNAIRE inputs
                if q_name not in ["private", "info"]:
                    LOGGER.warning(
                        f"Unrecognised `redcap_repeat_instrument` value: {q_name}"
                    )
        out[record_id] = {"study_id": subset[0]["study_id"], **qr}
    return out


def get_true_colours_data(tc_dir: str) -> dict:
    tmp_dir = ".run"
    os.makedirs(tmp_dir, exist_ok=True)
    # unzip the archive
    subprocess.run(["unzip", "-o", tc_dir, "-d", tmp_dir], check=True)
    # We now have a directory of csv files (actually pipe-separated) we can load as a dict
    tc_data = parse_tc(tmp_dir)
    # Clean up
    subprocess.run(["rm", "-rf", tmp_dir], check=True)
    return tc_data


def compare_tc_to_rc(tc_data: dict, redcap_id_data: List[dict]) -> Tuple[dict, list]:
    """
    Compare the True Colours data to the REDCap data.
    
    :param tc_data: parsed data exported from True Colours
    :param redcap_id_data: parsed data exported from REDCap
    :return: a tuple of new_participants, new_responses
        new_participants is a dictionary of participant_id: {private, info} where private and info are dictionaries
        of data to be uploaded to REDCap. These need a new study_id generated by REDCap to be added before upload.
        new_responses is a list of dictionaries of data to be uploaded to REDCap. These may have study_id NEW x if
        they belong to a participant who is new where x is the participant id.
        This will need to be patched before upload.
    """
    # First, search for patients who don't have REDCap entries
    new_participants = {}
    for p in tc_data["patient.csv"]:
        if p.get("id") not in redcap_id_data:
            private, info = extract_participant_info(p)
            new_participants[p.get("id")] = {
                "private": private,
                "info": info,
            }
    # Next, check for new questionnaire responses
    new_responses = []
    for qr in tc_data["questionnaireresponse.csv"]:
        p_id = qr.get("patientid")
        q_id = qr.get("id")
        interop = qr.get("interoperability")
        if interop is None:
            LOGGER.warning(
                f"Questionnaire response id={q_id} missing interoperability field."
            )
            continue
        q_name = interop.get("title")
        questionnaire = get_questionnaire_by_name(q_name)
        if questionnaire is None:
            LOGGER.warning(
                f"Questionnaire response id={q_id} has unrecognised title {q_name}."
            )
            continue
        q_code = questionnaire.get("code")
        q_repeats = questionnaire.get("repeat_instrument", True)
        is_new = p_id not in redcap_id_data or q_id not in [
            x[0] for x in redcap_id_data[p_id][q_code]
        ]
        if is_new:
            if p_id not in redcap_id_data or len(redcap_id_data[p_id].get(q_code, list())) == 0:
                instance_number = 1
            else:
                instance_number = max([x[1] for x in redcap_id_data[p_id][q_code]]) + 1
            new_responses.append(
                {
                    "study_id": redcap_id_data[p_id]["study_id"] if p_id in redcap_id_data else f"__NEW__{p_id}",
                    # Add the redcap_repeat_* fields if the questionnaire repeats
                    **(
                        {
                            "redcap_repeat_instrument": q_code,
                            "redcap_repeat_instance": instance_number
                        } if q_repeats else {}
                    ),
                    **questionnaire_to_rc_record(qr),
                }
            )
    return new_participants, new_responses


def is_redcap_structure_valid(redcap_project: Project, raise_error: bool = False) -> Optional[bool]:
    """
    Check if the REDCap structure is valid. 
    This can only check if all the required fields are present, not that they belong to the appropriate instruments.
    It can also not check anything if there are no records in REDCap.
    In that case, it returns None rather than False.
    """
    required_structure = get_redcap_structure()
    redcap_structure = redcap_project.export_records()
    if len(redcap_structure) == 0:
        if raise_error:
            raise ValueError("No records found in REDCap")
        return None
    for r, v in required_structure.items():
        for var in v:
            if var not in redcap_structure[0].keys():
                if raise_error:
                    raise ValueError(f"Missing field {var} in REDCap structure.")
                return False
    return True


def get_response_id_from_response_data(response_data: dict) -> str:
    """
    Get the name of the field that contains the response id for a questionnaire response.
    
    If there's a redcap_repeat_instrument field, this will be the name of the field with the response id.
    If not, it'll be the only *_response_id field with an actual value.
    """
    if response_data.get("redcap_repeat_instrument") is not None:
        return response_data[f"{response_data['redcap_repeat_instrument']}_response_id"]
    response_id_fields = list(filter(lambda x: x.endswith("_response_id"), response_data.keys()))
    if len(response_id_fields) == 1:
        return response_data[response_id_fields[0]]
    if len(response_id_fields) == 0:
        raise ValueError("Can't determine response_id field name when no *_response_id fields contain data")
    raise ValueError((
        "Can't determine response_id field name when multiple *_response_id fields contain data:"
        f" {response_id_fields}"
    ))
