from datetime import datetime
from typing import Literal, Tuple, List

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


class QuestionnaireMetadata(TypedDict):
    name: str
    code: str
    items: List[str]  # QuestionShortName in TrueColours data
    scores: List[str]  # Name in TrueColours data


QUESTIONNAIRES: List[QuestionnaireMetadata] = [
    {
        "name": "MENTAL HEALTH MISSION MOOD DISORDER COHORT STUDY - Patient Information Sheet & Informed Consent Form",
        "code": "consent",
        "items": [],
        "scores": [],
    },
    {
        "name": "Demographics",
        "code": "demo",
        "items": [],
        "scores": [],
    },
    {
        "name": "Depression (PHQ-9)",
        "code": "phq9",
        "items": [
            "Interest",
            "Depression",
            "Sleep",
            "Lack of energy",
            "Appetite",
            "View of self",
            "Concentration",
            "Movements",
            "Self-harm",
        ],
        "scores": ["Total"],
    },
    {
        "name": "Anxiety (GAD-7)",
        "code": "gad7",
        "items": [
            "Anxious",
            "Uncontrollable worrying",
            "Excessive worrying",
            "Relaxing",
            "Restless",
            "Irritable",
            "Afraid",
            "Difficult",
        ],
        "scores": ["Total"],
    },
    {
        "name": "Mania (Altman)",
        "code": "mania",
        "items": [
            "+Happiness",
            "+Confidence",
            "-Sleep",
            "+Talking",
            "+Activity",
        ],
        "scores": ["Total"],
    },
    {
        "name": "ReQoL 10",
        "code": "reqol10",
        "items": [
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
        ],
        "scores": ["Total"],
    },
    {
        "name": "Work and Social Adjustment Scale",
        "code": "wsas",
        "items": [
            "Work",
            "Management",
            "Social leisure",
            "Private leisure",
            "Family",
        ],
        "scores": ["Total"],
    },
]


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


def convert_generic(questionnaire_response: dict) -> dict:
    questionnaire = list(
        filter(
            lambda q: q["name"] == questionnaire_response["interoperability"]["title"],
            QUESTIONNAIRES,
        )
    )[0]
    prefix = questionnaire["code"]
    out = {
        f"{prefix}_response_id": str(questionnaire_response["id"]),
        f"{prefix}_datetime": str(questionnaire_response["submitted"]),
    }
    scores = questionnaire_response["scores"]
    for i, k in enumerate(questionnaire["items"]):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        if not item:
            LOGGER.warning(f"{prefix}: No {k} in scores")
            continue
        if k.startswith("-"):
            out[f"{prefix}_{i + 1}_{convert_key(k[1:])}_float"] = str(item["Score"])
        else:
            out[f"{prefix}_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in questionnaire["scores"]:
        score = next((x for x in category_scores if x["Name"] == c), None)
        if not score:
            LOGGER.warning(f"{prefix}: No {c} in category scores")
            continue
        out[f"{prefix}_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


def to_rc_record(metadata: RCRecordMetadata, data: dict):
    return {**metadata, **data}


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
