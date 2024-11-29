from datetime import datetime
from typing import Literal, Tuple, List, Callable

from typing_extensions import TypedDict

# Fetch a logger so we can log messages
import logging

LOGGER = logging.getLogger(__name__)


def convert_key(key: str) -> str:
    return key.lower().strip().replace("-", "_").replace(" ", "_").replace("+", "")


class RCRecordMetadata(TypedDict):
    study_id: str
    redcap_repeat_instrument: Literal["demo", "consent", "phq9", "private"]
    redcap_repeat_instance: int


class QuestionnaireMetadata(TypedDict):
    name: str
    code: str
    items: List[str]  # QuestionShortName in TrueColours data
    scores: List[str]  # Name in TrueColours data
    conversion_fn: Callable[["QuestionnaireMetadata", dict], dict]


def convert_consent(_q: QuestionnaireMetadata, questionnaire_data: dict) -> dict:
    question_scores = questionnaire_data["scores"]["QuestionScores"]
    out = {
        "consent_response_id": str(questionnaire_data["id"]),
        "consent_datetime": questionnaire_data["submitted"],
    }
    for q in [
        *list(range(17)),
        18,
    ]:  # Question 18 is not reported because it's a signature
        question = next(
            (x for x in question_scores if x["QuestionNumber"] == q + 1), None
        )
        out[f"consent_{q + 1}_str"] = question["DisplayValue"]

    return out


def convert_display_values(questionnaire: QuestionnaireMetadata, questionnaire_response: dict) -> dict:
    """
    Convert a questionnaire where we take the text of the answers rather than the scores.
    """
    prefix = questionnaire["code"]
    out = {
        f"{prefix}_response_id": str(questionnaire_response["id"]),
        f"{prefix}_datetime": str(
            questionnaire_response["interoperability"]["submitted"]
        ),
    }
    scores = questionnaire_response["scores"]
    for i, k in enumerate(questionnaire["items"]):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionNumber"] == i + 1), None
        )
        if not item:
            LOGGER.warning(f"{prefix}: No {k} in scores")
            continue
        out[f"{prefix}_{i + 1}_{k}_str"] = str(item["DisplayValue"])

    return out


def convert_scores(questionnaire: QuestionnaireMetadata, questionnaire_response: dict) -> dict:
    """
    Convert a questionnaire where we take the scores of the answers.
    """
    prefix = questionnaire["code"]
    out = {
        f"{prefix}_response_id": str(questionnaire_response["id"]),
        f"{prefix}_datetime": str(
            questionnaire_response["interoperability"]["submitted"]
        ),
    }
    scores = questionnaire_response["scores"]
    for i, k in enumerate(questionnaire["items"]):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionNumber"] == i + 1), None
        )
        if not item:
            LOGGER.warning(f"{prefix}: No {k} in scores")
            continue
        out[f"{prefix}_{i + 1}_{k}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in questionnaire["scores"]:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"{prefix}: No {c} in category scores")
            continue
        out[f"{prefix}_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


def extract_participant_info(patient_csv_data: dict) -> Tuple[dict, dict]:
    """
    Extract participant info from CSV file.

    Return a dict of `private` information and public `info`rmation.
    """
    def is_test_nhs_number(nhs_number: str) -> bool:
        return nhs_number.startswith("999")
    
    keep_fields = [
        "id",
        "nhsnumber",
        "birthdate",
        "contactemail",
        "mobilenumber",
        "firstname",
        "lastname",
        "preferredcontact",
    ]
    now = datetime.now().isoformat()

    return {
        # YYYY-MM-DD HH:MM:SS.sss format of the current date
        "datetime": now,
        **{k: v for k, v in patient_csv_data.items() if k in keep_fields},
    }, {
        "info_datetime": now,
        "info_birthyear_int": patient_csv_data.get("birthdate").split("-")[0],
        "info_gender_int": patient_csv_data.get("gender"),
        "info_is_test_bool": is_test_nhs_number(patient_csv_data.get("nhsnumber")),
        "info_is_deceased_bool": patient_csv_data.get("deceasedboolean"),
        "info_deceased_datetime": patient_csv_data.get("deceaseddatetime"),
    }
