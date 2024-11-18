from trd_cli.main_functions import compare_tc_to_rc


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
        
    # Dump a list of the variables REDCap needs to have available to import data.
    # This aids in setting up the REDCap project.
    pp, rr = compare_tc_to_rc(parse_tc("."), redcap_id_data=list())
    rc_variables_list = {}
    for p in pp.values():
        rc_variables_list["private"] = set(p["private"].keys())
        rc_variables_list["info"] = set(p["info"].keys())
        break
    for r in rr:
        if r["redcap_repeat_instrument"] not in rc_variables_list:
            rc_variables_list[r["redcap_repeat_instrument"]] = set(r.keys())
        else:
            [rc_variables_list[r["redcap_repeat_instrument"]].add(k) for k in r.keys()]
            
    redcap_vars = ["study_id", "redcap_repeat_instrument", "redcap_repeat_instance"]
    for k, v in rc_variables_list.items():
        rc_variables_list[k] = [x for x in v if x not in redcap_vars]
    with open("./rc_variables.txt", "w+") as f:
        f.flush()
        for k in rc_variables_list.keys():
            f.write(f"###### {k} ######\n")
            vv = sorted(rc_variables_list[k])
            for x in vv:
                f.write(f"{x}\n")
            f.write("\n")
