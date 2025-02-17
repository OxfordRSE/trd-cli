from typing import List, Dict, Union

from trd_cli.conversions import QuestionnaireMetadata, convert_scores, convert_display_values, convert_consent, \
    RCRecordMetadata, extract_participant_info

# List of questionnaires with their metadata
# Each questionnaire has a name, code, list of items, list of scores, and a conversion function
# Questionnaires may have a "repeat_instrument" field to indicate whether they are repeated (default is True)
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
            "Total"
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
        "repeat_instrument": False,
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
            "physical_health",  # sic
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


def to_rc_record(metadata: RCRecordMetadata, data: dict):
    return {**metadata, **data}


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


def get_redcap_structure() -> Dict[str, List[str]]:
    """
    Map the required REDCap structure to a dict of {"instrument": [fields]}.
    """
    dump = {}
    # The participant data is a special case because it's not a questionnaire
    dummy_participant = {
        "id": "1234567890",
        "nhsnumber": "1234567890",
        "birthdate": "YYYY-MM-DD",
        "contactemail": "",
        "mobilenumber": "",
        "firstname": "",
        "lastname": "",
        "preferredcontact": "",
        "deceasedboolean": "",
        "deceaseddatetime": "",
        "gender": "",
    }
    dump["private"], dump["info"] = extract_participant_info(dummy_participant)
    
    consent_q = list(filter(lambda x: x["code"] == "consent", QUESTIONNAIRES))[0]
    consent_data = {
        "id": "1234567890",
        "submitted": "YYYY-MM-DD HH:MM:SS.sss",
        "interoperability": {
            "submitted": "YYYY-MM-DD HH:MM:SS.sss",
            "title": consent_q["name"],
        },
        "scores": {
            "QuestionScores": [
                {"QuestionNumber": i + 1, "Score": "0", "DisplayValue": "Answer"} for i in range(18)
            ]
        },
    }
    # Consent's penultimate question is a signature that isn't exported 
    consent_data["scores"]["QuestionScores"][-1]["QuestionNumber"] += 1
    dump["consent"] = convert_consent(consent_q, consent_data)
    
    for q in QUESTIONNAIRES:
        # Special case for 'consent' questionnaire where Q17 is a non-exported signature
        if q["code"] == "consent":
            continue
        # Mock questionnaire data with reference to its declaration
        dummy_questionnaire = {
            "id": "1234567890",
            "submitted": "YYYY-MM-DD HH:MM:SS.sss",
            "interoperability": {
                "submitted": "YYYY-MM-DD HH:MM:SS.sss",
                "title": q["name"],
            },
            "scores": {
                "QuestionScores": [
                    {"QuestionNumber": i + 1, "Score": "0", "DisplayValue": "Answer"} for i in range(len(q["items"]))
                ],
                "CategoryScores": [
                    {"Name": c, "Score": 0} for c in q["scores"]
                ],
            },
        }
        dump[q["code"]] = q["conversion_fn"](q, dummy_questionnaire)
    
    for k, v in dump.items():
        dump[k] = list(v.keys())
    
    return dump


def dump_redcap_structure(filename: Union[str, None]):
    """
    Dump the REDCap structure to a file.
    This is useful for setting up REDCap to handle the incoming data.
    """
    dump = get_redcap_structure()
    lines = []
    for k in dump.keys():
        lines.append(f"###### {k} ######")
        vv = sorted(dump[k])
        for x in vv:
            lines.append(f"{x}")
        lines.append("")

    if filename is None:
        print("\n".join(lines))
    else:
        with open(filename, "w+") as f:
            f.write("\n".join(lines))


def get_questionnaire_by_name(name: str) -> Union[QuestionnaireMetadata, None]:
    qs = [q for q in QUESTIONNAIRES if q["name"] == name]
    if len(qs) == 0:
        return None
    return qs[0]
