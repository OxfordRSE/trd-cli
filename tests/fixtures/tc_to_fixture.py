

def patient_to_fixture(patient_csv_data: dict) -> dict:
    """
    Return a dictionary of redacted patient data.
    """
    okay_fields = [
        "id", "nhsnumber", "birthdate", "gender", "firstname", "lastname", "mobilenumber", "contactemail",
        "deceasedboolean", "deceaseddatetime", "preferredcontact"
    ]
    return {k: v for k, v in patient_csv_data.items() if k in okay_fields}


def questionnaire_to_fixture(questionnaire_response: dict) -> dict:
    """
    Return a dictionary of redacted questionnaire response data.
    """
    okay_fields = [
        "id", "questionnaireid", "patientid", "responses", "scores", "submitted", "interoperability"
    ]
    return {k: v for k, v in questionnaire_response.items() if k in okay_fields}


def tc_to_fixture(tc_data: dict) -> dict:
    """
    Return a dictionary of redacted True Colours data.
    """
    out_data = {}
    out_data["patient.csv"] = list(map(patient_to_fixture, tc_data["patient.csv"]))
    out_data["questionnaireresponse.csv"] = list(
        filter(lambda x: x["responses"] is not None, tc_data["questionnaireresponse.csv"])
    )
    out_data["questionnaireresponse.csv"] = list(
        map(questionnaire_to_fixture, out_data["questionnaireresponse.csv"])
    )

    return out_data


if __name__ == "__main__":
    import json
    from trd_cli.parse_tc import parse_tc
    with open("./tc_data.json", "w+") as f:
        json.dump(tc_to_fixture(parse_tc(".")), f, indent=4)
    with open("./tc_data_initial.json", "w+") as f:
        json.dump(parse_tc("./initial_tc_dump"), f, indent=4)
