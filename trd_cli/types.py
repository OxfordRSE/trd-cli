from typing import Optional, Literal, TypeVar, Generic, Any
from typing_extensions import TypedDict


class TCQRInteroperabilityCategoryScore(TypedDict):
    Name: str
    Score: float
    MaxScore: float
    Tscore: Optional[float]
    ScoreStatus: int
    IsTotal: bool
    DisplayValue: str


QShortName = TypeVar("QShortName", bound=str)


class TCQRInteroperabilityQuestionScore(TypedDict, Generic[QShortName]):
    QuestionNumber: int
    QuestionShortName: QShortName
    Score: float
    MaxScore: float
    DisplayValue: str


class TCQRInterpoperabilityScores(TypedDict):
    CategoryScores: Optional[list[TCQRInteroperabilityCategoryScore]]
    QuestionScores: list[TCQRInteroperabilityQuestionScore]


class TCQRInteroperatbility(TypedDict):
    version: int
    scores: TCQRInterpoperabilityScores
    submitted: str
    questionnaireid: int
    id: int
    tenant: str
    patientid: Optional[int]
    title: str
    type: Literal["Questionnaire"]
    active: bool


class RCQRDataRaw(TypedDict):
    study_id: int
    # TC patient
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
    demo_birthyear_int: str
    demo_gender_int: str
    demo_is_deceased_bool: str
    demo_deceased_datetime_datetime: str
    # TC PHQ-9
    phq9_meta_datetime_datetime: str
    phq9_1_interest_int: str
    phq9_2_depression_int: str
    phq9_3_sleep_int: str
    phq9_4_lack_of_energy_int: str
    phq9_5_appetite_int: str
    phq9_6_view_of_self_int: str
    phq9_7_concentration_int: str
    phq9_8_movements_int: str
    phq9_9_self_harm_int: str
    phq9_score_total: str


class RCQRData(TypedDict):
    study_id: int
    # TC patient
    id: int  # patient.id NOT patient.userid
    nhsnumber: str
    birthdate: str
    contactemail: str
    mobilenumber: str
    firstname: str
    lastname: str
    preferredcontact: int
    # active: bool
    created: str
    updated: str
    demo_birthyear: int
    demo_gender: int
    demo_is_deceased: bool
    demo_deceased_datetime: str
    # TC PHQ-9
    phq9_meta_datetime: str
    phq9_1_interest: int
    phq9_2_depression: int
    phq9_3_sleep: int
    phq9_4_lack_of_energy: int
    phq9_5_appetite: int
    phq9_6_view_of_self: int
    phq9_7_concentration: int
    phq9_8_movements: int
    phq9_9_self_harm: int
    phq9_score_total: int


QUESTIONNAIRES = {
    "Depression (PHQ-9)": {
        "Interest": "phq9_1_interest_int",
        "Depression": "phq9_2_depression_int",
        "Sleep": "phq9_3_sleep_int",
        "Lack of energy": "phq9_4_lack_of_energy_int",
        "Appetite": "phq9_5_appetite_int",
        "View of self": "phq9_6_view_of_self_int",
        "Concentration": "phq9_7_concentration_int",
        "Movements": "phq9_8_movements_int",
        "Self-harm": "phq9_9_self_harm_int",
    }
}


def convert_key(key: str) -> str:
    return key.lower().strip().replace("-", "_").replace(" ", "_")


def convert_int(value: Any) -> str:
    return str(int(value))


def phq9_to_rc(study_id: int, data: TCQRInteroperatbility) -> RCQRDataRaw:
    scores = data["scores"]
    out = {"study_id": study_id}
    for k, v in QUESTIONNAIRES["Depression (PHQ-9)"].items():
        item = next(
            (x for x in scores["QuestionScores"] if x["QuestionShortName"] == k), None
        )
        out[v] = convert_int(item["Score"]) if item else None
    # Append scores
    category_scores = scores["CategoryScores"]
    for category_score in category_scores:
        out[f"phq9_score_{convert_key(category_score['Name'])}_int"] = convert_int(
            category_score["Score"]
        )
    return out
