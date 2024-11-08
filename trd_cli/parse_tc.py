import csv
import json
import os
import logging

LOGGER = logging.getLogger(__name__)


def parse_responses(questionnaire_response_data: list) -> list:
    """
    Return `questionnaire_response_data` with the response fields json-parsed.
    The second return is a list of warnings generated during processing.
    """
    for i, row in enumerate(questionnaire_response_data):
        for k, v in row.items():
            if k in ["responses", "scores", "interoperability"]:
                if v == "":
                    row[k] = None
                    continue
                try:
                    row[k] = json.loads(v)
                except json.JSONDecodeError as e:
                    LOGGER.warning(f"L{i}:{k} - {e}{' | ' + v if v else '[Empty]'}")
    return questionnaire_response_data


def parse_tc(tc_dir: str) -> dict:
    """
    Return a dictionary of parsed .csv files in a True Colours export directory.
    The second return is a list of warnings generated during processing.
    """
    tc_data = {}
    files = os.listdir(tc_dir)
    for file in list(filter(lambda x: x.endswith(".csv"), files)):
        with open(os.path.join(tc_dir, file), "r") as f:
            data = list(csv.DictReader(f, delimiter="|"))
            if file == "questionnaireresponse.csv":
                data = parse_responses(data)
            tc_data[os.path.basename(file)] = data
    return tc_data
