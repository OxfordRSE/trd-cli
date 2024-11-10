import csv
import json
from datetime import datetime
from unittest import TestCase, main

from trd_cli.conversions import convert_questionnaire, extract_participant_info


class ConversionsTest(TestCase):
    def test_phq9(self):
        qr_file = "fixtures/questionnaireresponse.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            for response in responses:
                if not isinstance(response, dict):
                    continue
                io = response.get("interoperability")
                try:
                    io = json.loads(io)
                except json.JSONDecodeError:
                    continue
                if io.get("title") == "Depression (PHQ-9)":
                    self.assertEqual(
                        {
                            "phq9_response_id": "1589930675",
                            "phq9_datetime": "2024-11-04T12:59:24.9477348+00:00",
                            "phq9_1_interest_float": "3.0",
                            "phq9_2_depression_float": "3.0",
                            "phq9_3_sleep_float": "3.0",
                            "phq9_4_lack_of_energy_float": "3.0",
                            "phq9_5_appetite_float": "3.0",
                            "phq9_6_view_of_self_float": "3.0",
                            "phq9_7_concentration_float": "3.0",
                            "phq9_8_movements_float": "3.0",
                            "phq9_9_self_harm_float": "3.0",
                            "phq9_score_total_float": "27.0",
                        },
                        convert_questionnaire(io),
                    )
                    return
        self.fail(f"No PHQ-9 questionnaire found in {qr_file}")

    def test_gad9(self):
        qr_file = "fixtures/questionnaireresponse.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            for response in responses:
                if not isinstance(response, dict):
                    continue
                io = response.get("interoperability")
                try:
                    io = json.loads(io)
                except json.JSONDecodeError:
                    continue
                if io.get("title") == "Anxiety (GAD-7)":
                    self.assertEqual(
                        {
                            "gad7_response_id": "453451573",
                            "gad7_1_anxious_float": "2.0",
                            "gad7_2_uncontrollable_worrying_float": "2.0",
                            "gad7_3_excessive_worrying_float": "1.0",
                            "gad7_4_relaxing_float": "1.0",
                            "gad7_5_restless_float": "1.0",
                            "gad7_6_irritable_float": "2.0",
                            "gad7_7_afraid_float": "3.0",
                            "gad7_8_difficult_float": "0.0",
                            "gad7_datetime": "2024-11-05T12:05:43.5629631+00:00",
                            "gad7_score_total_float": "12.0",
                        },
                        convert_questionnaire(io),
                    )
                    return
        self.fail(f"No GAD-7 questionnaire found in {qr_file}")

    def test_mania(self):
        qr_file = "fixtures/questionnaireresponse.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            for response in responses:
                if not isinstance(response, dict):
                    continue
                io = response.get("interoperability")
                try:
                    io = json.loads(io)
                except json.JSONDecodeError:
                    continue
                if io.get("title") == "Mania (Altman)":
                    self.assertEqual(
                        {
                            "mania_response_id": "976453020",
                            "mania_1_happiness_float": "1.0",
                            "mania_2_confidence_float": "1.0",
                            "mania_3_sleep_float": "1.0",
                            "mania_4_talking_float": "1.0",
                            "mania_5_activity_float": "2.0",
                            "mania_datetime": "2024-11-05T12:05:59.3055890+00:00",
                            "mania_score_total_float": "6.0",
                        },
                        convert_questionnaire(io),
                    )
                    return
        self.fail(f"No Mania questionnaire found in {qr_file}")

    def test_reqol10(self):
        qr_file = "fixtures/questionnaireresponse.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            for response in responses:
                if not isinstance(response, dict):
                    continue
                io = response.get("interoperability")
                try:
                    io = json.loads(io)
                except json.JSONDecodeError:
                    continue
                if io.get("title") == "ReQoL 10":
                    self.assertEqual(
                        {
                            "reqol10_response_id": "1504524233",
                            "reqol10_datetime": "2024-11-05T12:07:38.7956557+00:00",
                            "reqol10_1_everyday_tasks_float": "3.0",
                            "reqol10_2_trust_others_float": "2.0",
                            "reqol10_3_unable_to_cope_float": "1.0",
                            "reqol10_4_do_wanted_things_float": "2.0",
                            "reqol10_5_felt_happy_float": "4.0",
                            "reqol10_6_not_worth_living_float": "2.0",
                            "reqol10_7_enjoyed_float": "3.0",
                            "reqol10_8_felt_hopeful_float": "3.0",
                            "reqol10_9_felt_lonely_float": "2.0",
                            "reqol10_10_confident_in_self_float": "2.0",
                            "reqol10_11_pysical_health_float": "4.0",
                            "reqol10_score_total_float": "24.0",
                        },
                        convert_questionnaire(io),
                    )
                    return
        self.fail(f"No ReQoL 10 questionnaire found in {qr_file}")

    def test_wsas(self):
        qr_file = "fixtures/questionnaireresponse.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            for response in responses:
                if not isinstance(response, dict):
                    continue
                io = response.get("interoperability")
                try:
                    io = json.loads(io)
                except json.JSONDecodeError:
                    continue
                if io.get("title") == "Work and Social Adjustment Scale":
                    self.assertEqual(
                        {
                            "wsas_response_id": "1212115884",
                            "wsas_datetime": "2024-11-05T12:08:48.0135908+00:00",
                            "wsas_1_work_float": "3.0",
                            "wsas_2_management_float": "5.0",
                            "wsas_3_social_leisure_float": "3.0",
                            "wsas_4_private_leisure_float": "5.0",
                            "wsas_5_family_float": "5.0",
                            "wsas_score_total_float": "21.0",
                        },
                        convert_questionnaire(io),
                    )
                    return
        self.fail(f"No WSAS questionnaire found in {qr_file}")

    def test_extract_info(self):
        qr_file = "fixtures/patient.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            response = next(responses)
        private, public = extract_participant_info(response)
        self.assertGreater(datetime.now().isoformat(), private["datetime"])
        self.assertGreater(datetime.now().isoformat(), public["info_datetime"])
        private["datetime"] = None
        public["info_datetime"] = None
        self.assertEqual(
            {
                "birthdate": "1949-11-04",
                "contactemail": "b.tester@example.com",
                "firstname": "Besty",
                "id": "1255217154",
                "datetime": None,
                "lastname": "Tester",
                "mobilenumber": "+44 7000 000000",
                "nhsnumber": "9910362813",
                "preferredcontact": "0",
            },
            private,
        )
        self.assertEqual(
            {
                "info_birthyear_int": "1949",
                "info_datetime": None,
                "info_deceased_datetime": "",
                "info_gender_int": "1",
                "info_is_deceased_bool": "",
            },
            public,
        )


if __name__ == "__main__":
    main()
