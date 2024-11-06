import csv
import json
import os
from typing import Tuple

def parse_responses(questionnaire_response_data: dict) -> Tuple[dict, list]:
    """
    Return `questionnaire_response_data` with the response fields json-parsed.
    The second return is a list of warnings generated during processing.
    """
    warnings = []
    for i, row in enumerate(questionnaire_response_data):
        for k, v in row.items():
            if k in ["responses", "scores", "interoperability"]:
                if v == "":
                    row[k] = None
                    continue
                try:
                    row[k] = json.loads(v)
                except json.JSONDecodeError as e:
                    warnings.append(
                        f"L{i}:{k} - {e}{' | ' + v if v else '[Empty]'}"
                    )
    return questionnaire_response_data, warnings



def parse_tc(tc_dir: str) -> Tuple[dict, list]:
    """
    Return a dictionary of parsed .csv files in a True Colours export directory.
    The second return is a list of warnings generated during processing.
    """
    warnings = []
    tc_data = {}
    files = os.listdir(tc_dir)
    for file in list(filter(lambda x: x.endswith(".csv"), files)):
        with open(os.path.join(tc_dir, file), "r") as f:
            data = list(csv.DictReader(f, delimiter="|"))
            if file == "questionnaireresponse.csv":
                data, new_warnings = parse_responses(data)
                for w in new_warnings:
                    warnings.append(
                        f"{os.path.basename(file)}:{w}"
                    )
            tc_data[os.path.basename(file)] = data
    return tc_data, warnings