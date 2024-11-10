from datetime import datetime
from typing import Literal, Tuple

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


class RCRecordRow(RCRecordMetadata):
    # Private information. Types not included because users will not see this.
    id: str  # patient.id NOT patient.userid
    nhsnumber: str
    birthdate: str
    contactemail: str
    mobilenumber: str
    firstname: str
    lastname: str
    preferredcontact: str
    # active: bool
    created: str
    updated: str
    # Consent
    # Demo (Demographics)
    demo_birthyear_int: str
    demo_gender_int: str
    demo_is_deceased_bool: str
    demo_deceased_datetime: str
    # PHQ9 (Depression)
    phq9_response_id: str
    phq9_datetime: str
    phq9_1_interest_float: str
    phq9_2_depression_float: str
    phq9_3_sleep_float: str
    phq9_4_lack_of_energy_float: str
    phq9_5_appetite_float: str
    phq9_6_view_of_self_float: str
    phq9_7_concentration_float: str
    phq9_8_movements_float: str
    phq9_9_self_harm_float: str
    phq9_score_total_float: str
    # GAD7 (Anxiety)
    gad7_response_id: str
    gad7_datetime: str
    gad7_1_anxious_float: str
    gad7_2_uncontrollable_worrying_float: str
    gad7_3_excessive_worrying_float: str
    gad7_4_relaxing_float: str
    gad7_5_restless_float: str
    gad7_6_irritable_float: str
    gad7_7_afraid_float: str
    gad7_8_difficult_float: str
    gad7_score_total_float: str
    # Mania (Altman)
    mania_response_id: str
    mania_datetime: str
    mania_1_happiness_float: str
    mania_2_confidence_float: str
    mania_3_sleep_float: str
    mania_4_talking_float: str
    mania_5_activity_float: str
    mania_score_total_float: str
    # ReQoL 10
    reqol10_response_id: str
    reqol10_datetime: str
    reqol10_1_everyday_tasks_float: str
    reqol10_2_trust_others_float: str
    reqol10_3_unable_to_cope_float: str
    reqol10_4_do_wanted_things_float: str
    reqol10_5_felt_happy_float: str
    reqol10_6_not_worth_living_float: str
    reqol10_7_enjoyed_float: str
    reqol10_8_felt_hopeful_float: str
    reqol10_9_felt_lonely_float: str
    reqol10_10_confident_in_self_float: str
    reqol10_11_pysical_health_float: str
    reqol10_score_total_float: str
    # Work and Social Adjustment Scale (WSAS)
    wsas_response_id: str
    wsas_datetime: str
    wsas_1_work_float: str
    wsas_2_management_float: str
    wsas_3_social_leisure_float: str
    wsas_4_private_leisure_float: str
    wsas_5_family_float: str
    wsas_score_total_float: str


def convert_private(data: dict) -> dict:
    return {}


def convert_consent(data: dict) -> dict:
    out = {
        "consent_datetime": data["submitted"],
    }
    for q in [
        *list(range(17)),
        18,
    ]:  # Question 18 is not reported because it's a signature
        question = next(
            (x for x in data["scores"] if x["QuestionNumber"] == q + 1), None
        )
        out[f"consent_{q + 1}_str"] = question["DisplayValue"]

    return {}


def convert_demo(data: dict) -> dict:
    return {
        "demo_birthyear_int": str(),
        "demo_gender_int": str(),
        "demo_is_deceased_bool": str(),
        "demo_deceased_datetime": str(),
    }


# True Colours item ShortNames for PHQ9
PHQ9_ITEMS = [
    "Interest",
    "Depression",
    "Sleep",
    "Lack of energy",
    "Appetite",
    "View of self",
    "Concentration",
    "Movements",
    "Self-harm",
]
# True Colours score Names for PHQ9
PHQ9_SCORES = ["Total"]


def convert_phq9(data: dict) -> dict:
    scores = data["scores"]
    out = {"phq9_response_id": str(data["id"]), "phq9_datetime": str(data["submitted"])}
    for i, k in enumerate(PHQ9_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"PHQ9: No {k} in scores")
            continue
        out[f"phq9_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in PHQ9_SCORES:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"PHQ9: No {c} in category scores")
            continue
        out[f"phq9_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


GAD7_ITEMS = [
    "Anxious",
    "Uncontrollable worrying",
    "Excessive worrying",
    "Relaxing",
    "Restless",
    "Irritable",
    "Afraid",
    "Difficult",
]
GAD7_SCORES = ["Total"]


def convert_gad7(data: dict) -> dict:
    scores = data["scores"]
    out = {"gad7_response_id": str(data["id"]), "gad7_datetime": str(data["submitted"])}
    for i, k in enumerate(GAD7_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"GAD7: No {k} in scores")
            continue
        out[f"gad7_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in GAD7_SCORES:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"GAD7: No {c} in category scores")
            continue
        out[f"gad7_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


MANIA_ITEMS = [
    "+Happiness",
    "+Confidence",
    "-Sleep",
    "+Talking",
    "+Activity",
]
MANIA_SCORES = ["Total"]


def convert_mania(data: dict) -> dict:
    scores = data["scores"]
    out = {
        "mania_response_id": str(data["id"]),
        "mania_datetime": str(data["submitted"]),
    }
    for i, k in enumerate(MANIA_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"Mania: No {k} in scores")
            continue
        key = (
            convert_key(k) if k != "-Sleep" else "sleep"
        )  # - is usually converted to _
        out[f"mania_{i + 1}_{key}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in MANIA_SCORES:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"Mania: No {c} in category scores")
            continue
        out[f"mania_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


REQL10_ITEMS = [
    "everyday tasks",
    "trust others",
    "unable to cope",
    "do wanted things",
    "felt happy",
    "not worth living",
    "enjoyed",
    "felt hopeful",
    "felt lonely",
    "confident in self",
    "pysical health",  # sic
]
REQL10_SCORES = ["Total"]


def convert_reqol10(data: dict) -> dict:
    scores = data["scores"]
    out = {
        "reqol10_response_id": str(data["id"]),
        "reqol10_datetime": str(data["submitted"]),
    }
    for i, k in enumerate(REQL10_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"ReQoL10: No {k} in scores")
            continue
        out[f"reqol10_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in REQL10_SCORES:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"ReQoL10: No {c} in category scores")
            continue
        out[f"reqol10_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


WSAS_ITEMS = [
    "Work",
    "Management",
    "Social leisure",
    "Private leisure",
    "Family",
]
WSAS_SCORES = ["Total"]


def convert_wsas(data: dict) -> dict:
    scores = data["scores"]
    out = {"wsas_response_id": str(data["id"]), "wsas_datetime": str(data["submitted"])}
    for i, k in enumerate(WSAS_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"WSAS: No {k} in scores")
            continue
        out[f"wsas_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in WSAS_SCORES:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"WSAS: No {c} in category scores")
            continue
        out[f"wsas_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


def to_rc_record(metadata: RCRecordMetadata, data: dict):
    return {**metadata, **data}


questionnaire_conversions = {
    "MENTAL HEALTH MISSION MOOD DISORDER COHORT STUDY - Patient Information Sheet & Informed Consent Form": convert_consent,
    "Demographics": convert_consent,
    "Depression (PHQ-9)": convert_phq9,
    "Anxiety (GAD-7)": convert_gad7,
    "Mania (Altman)": convert_mania,
    "ReQoL 10": convert_reqol10,
    "Work and Social Adjustment Scale": convert_wsas,
}


def convert_questionnaire(interoperability_data: dict) -> dict:
    fn = questionnaire_conversions[interoperability_data["title"]]
    return fn(interoperability_data)


def extract_participant_info(patient_csv_data: dict) -> Tuple[dict, dict]:
    """
    Extract participant info from CSV file.

    Return a dict of `private` information and public `info`rmation.
    """
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
        "info_is_deceased_bool": patient_csv_data.get("deceasedboolean"),
        "info_deceased_datetime": patient_csv_data.get("deceaseddatetime"),
    }
