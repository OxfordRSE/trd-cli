from typing import Optional, Literal, TypeVar, Generic, Any, Union

from redcap import Project
from typing_extensions import TypedDict


def convert_key(key: str) -> str:
    return key.lower().strip().replace("-", "_").replace(" ", "_")


class RCInstrument(TypedDict):
    study_id: str
    redcap_repeat_instrument: Literal["demo", "consent", "phq9", "private"]
    redcap_repeat_instance: int


class RCPrivate(TypedDict):
    id: int  # patient.id NOT patient.userid
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


class RCConsent(TypedDict):
    pass


class RCDemo(TypedDict):
    # TC patient
    demo_birthyear_int: str
    demo_gender_int: str
    demo_is_deceased_bool: str
    demo_deceased_datetime: str

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


def to_rc_record(
        metadata: RCInstrument,
        data: dict
):
    return {**metadata, **data}


def convert_consent(data: dict) -> RCConsent:
    return {}


questionnaire_conversions = {
    "MENTAL HEALTH MISSION MOOD DISORDER COHORT STUDY - Patient Information Sheet & Informed Consent Form": convert_consent,
    "Demographics": convert_consent,
    "Depression (PHQ-9)": convert_phq9,
}


def convert_questionnaire(data: dict) -> dict:
    fn = questionnaire_conversions[data["title"]]
    return fn(data)
