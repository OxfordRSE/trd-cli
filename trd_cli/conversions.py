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


def get_code_by_name(name: str) -> str|None:
    qs = [q["code"] for q in QUESTIONNAIRES if q["name"] == name]
    if len(qs) == 0:
        return None
    return qs[0]


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


def to_rc_record(metadata: RCRecordMetadata, data: dict):
    return {**metadata, **data}


QUESTIONNAIRES: List[QuestionnaireMetadata] = [
    {
        "name": "Anxiety (GAD-7)",
        "code": "gad7",
        "items": [
            "anxious",
            "uncontrollable_worrying",
            "excessive_worrying",
            "relaxing",
            "restless",
            "irritable",
            "afraid",
            "difficult",
        ],
        "scores": ["Total"],
        "conversion_fn": convert_scores,
    },
    {
        "name": "AQ-10 Autistm Spectrum Quotient (AQ)",
        "code": "aq10",
        "items": [
            "sounds",
            "holism",
            "multitasking",
            "task_switching",
            "social_inference",
            "detect_boredom",
            "intentions_story",
            "collections",
            "facial_emotions",
            "intentions_real"
        ],
        "scores": [
            "Scoring 1"
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Adult ADHD Self-Report Scale (ASRS-v1.1) Symptom Checklist Instructions",
        "code": "asrs",
        "items": [
            "completing",
            "preparing",
            "remembering",
            "procrastination",
            "fidgeting",
            "overactivity",
            "carelessness",
            "attention",
            "concentration",
            "misplacing",
            "distracted",
            "standing",
            "restlessness",
            "not_relaxing",
            "loquacity",
            "finishing_sentences",
            "queueing",
            "interrupting",
        ],
        "scores": [],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Alcohol use disorders identification test (AUDIT)",
        "code": "audit",
        "items": [
            "frequency",
            "units",
            "binge_frequency",
            "cant_stop",
            "incapacitated",
            "morning_drink",
            "guilt",
            "memory_loss",
            "injuries",
            "concern",
        ],
        "scores": [
            "Low Risk",
            "Increased Risk",
            "Higher Risk",
            "Possible Dependence",
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Brooding subscale of Ruminative Response Scale",
        "code": "brss",
        "items": [
            "deserve",
            "react",
            "regret",
            "why_me",
            "handle"
        ],
        "scores": [
            "Scoring 1"
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Demographics",
        "code": "demo",
        "items": [
            "disabled",
            "long_term_condition",
            "national_identity",
            "national_identity_other",
            "ethnicity",
            "ethnicity_asian_detail",
            "ethnicity_asian_other",
            "ethnicity_black_detail",
            "ethnicity_black_other",
            "ethnicity_mixed_detail",
            "ethnicity_mixed_other",
            "ethnicity_white_detail",
            "ethnicity_white_other",
            "ethnicity_other_detail",
            "ethnicity_other_other",
            "religion",
            "religion_other",
            "sex",
            "gender",
            "gender_other",
            "trans",
            "sexuality",
            "sexuality_other",
            "relationship",
            "relationship_other",
            "caring",
            "employment",
            "employment_other",
            "education",
            "education_other",
        ],
        "scores": [],
        "conversion_fn": convert_display_values,
    },
    {
        "name": "Depression (PHQ-9)",
        "code": "phq9",
        "items": [
            "interest",
            "depression",
            "sleep",
            "lack_of_energy",
            "appetite",
            "view_of_self",
            "concentration",
            "movements",
            "self_harm",
        ],
        "scores": ["Total"],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Drug use disorders identification test (DUDIT)",
        "code": "dudit",
        "items": [
            "frequency",
            "multiple",
            "frequency_day",
            "influence",
            "longing",
            "cant_stop",
            "incapacitated",
            "morning_drug",
            "guilt",
            "injury",
            "concern"
        ],
        "scores": [
            "Scoring"
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Mania (Altman)",
        "code": "mania",
        "items": [
            "happiness",
            "confidence",
            "sleep",
            "talking",
            "activity",
        ],
        "scores": ["Total"],
        "conversion_fn": convert_scores,
    },
    {
        "name": "MENTAL HEALTH MISSION MOOD DISORDER COHORT STUDY - Patient Information Sheet & Informed Consent Form",
        "code": "consent",
        "items": [],
        "scores": [],
        "conversion_fn": convert_consent,
    },
    {
        "name": "Positive Valence Systems Scale, 21 items (PVSS-21)",
        "code": "pvss",
        "items": [
            "savour",
            "activities",
            "fresh_air",
            "social_time",
            "weekend",
            "touch",
            "outdoors",
            "feedback",
            "meals",
            "praise",
            "social_time",
            "goals",
            "hug",
            "fun",
            "hard_work",
            "meal",
            "achievements",
            "hug_afterglow",
            "mastery",
            "activities",
            "beauty",
        ],
        "scores": [
            "Food",
            "Physical Touch",
            "Outdoors",
            "Positive Feedback",
            "Hobbies",
            "Social Interactions",
            "Goals",
            "Reward Valuation",
            "Reward Expectancy",
            "Effort Valuation",
            "Reward Aniticipation",
            "Initial Responsiveness",
            "Reward Satiation"
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "ReQoL 10",
        "code": "reqol10",
        "items": [
            "everyday_tasks",
            "trust_others",
            "unable_to_cope",
            "do_wanted_things",
            "felt_happy",
            "not_worth_living",
            "enjoyed",
            "felt_hopeful",
            "felt_lonely",
            "confident_in_self",
            "pysical_health",  # sic
        ],
        "scores": ["Total"],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Standardised Assessment of Personality - Abbreviated Scale (Moran)",
        "code": "sapas",
        "items": [
            "friends",
            "loner",
            "trust",
            "temper",
            "impulsive",
            "worry",
            "dependent",
            "perfectionist",
        ],
        "scores": [
            "Scoring 1"
        ],
        "conversion_fn": convert_scores,
    },
    {
        "name": "Work and Social Adjustment Scale",
        "code": "wsas",
        "items": [
            "work",
            "management",
            "social_leisure",
            "private_leisure",
            "family",
        ],
        "scores": ["Total"],
        "conversion_fn": convert_scores,
    },
]

def questionnaire_to_rc_record(questionnaire_response: dict) -> dict:
    """
    Convert a questionnaire response to a REDCap record.
    """
    q_name = questionnaire_response["interoperability"]["title"]
    q = list(filter(lambda x: x["name"] == q_name, QUESTIONNAIRES))
    if len(q) == 0:
        # This should never happen because questionnaire_response will already have been vetted
        raise ValueError(f"Unrecognised questionnaire name {q_name}")
    else:
        q = q[0]
    return q["conversion_fn"](q, questionnaire_response)


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
