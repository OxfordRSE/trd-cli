from typing import Optional, Literal, TypeVar, Generic, Any, Union

from pydantic import TypeAdapter
from redcap import Project
from typing_extensions import TypedDict


def convert_key(key: str) -> str:
    return key.lower().strip().replace("-", "_").replace(" ", "_")


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


def convert_private(data: dict) -> dict:
    return {}


def convert_consent(data: dict) -> dict:
    out = {
        "consent_datetime": data["submitted"],
    }
    for q in [*list(range(17)), 18]:  # Question 18 is not reported because it's a signature
        question = next(
            (x for x in data['scores'] if x['QuestionNumber'] == q + 1), None
        )
        out[f"consent_{q + 1}_str"] = question['DisplayValue']

    return {

    }


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
    "Self-harm"
]
# True Colours score Names for PHQ9
PHQ9_SCORES = [
    "Total"
]

def convert_phq9(data: dict) -> dict:
    scores = data["scores"]
    out = {
        "phq9_datetime": str(data["submitted"])
    }
    for i, k in enumerate(PHQ9_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        out[f"phq9_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in PHQ9_SCORES:
        score = next(
            (x for x in category_scores if x["Name"] == c), None
        )
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
    "Difficult"
]
GAD7_SCORES = ["Total"]

def convert_gad7(data: dict) -> dict:
    scores = data["scores"]
    out = {
        "gad7_datetime": str(data["submitted"])
    }
    for i, k in enumerate(GAD7_ITEMS):
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        out[f"gad7_{i + 1}_{convert_key(k)}_float"] = str(item["Score"])

    # Append scores
    category_scores = scores["CategoryScores"]
    for c in GAD7_SCORES:
        score = next(
            (x for x in category_scores if x["Name"] == c), None
        )
        out[f"gad7_score_{convert_key(c)}_float"] = str(score["Score"])
    return out


def to_rc_record(
        metadata: RCRecordMetadata,
        data: dict
):
    return {**metadata, **data}


questionnaire_conversions = {
    "MENTAL HEALTH MISSION MOOD DISORDER COHORT STUDY - Patient Information Sheet & Informed Consent Form": convert_consent,
    "Demographics": convert_consent,
    "Depression (PHQ-9)": convert_phq9,
}


def convert_questionnaire(data: dict) -> dict:
    fn = questionnaire_conversions[data["title"]]
    return fn(data)
