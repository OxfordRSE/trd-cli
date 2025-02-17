import csv
from datetime import datetime
from time import sleep
from unittest import TestCase, main

from trd_cli.conversions import (
    extract_participant_info,
)
from trd_cli.questionnaires import questionnaire_to_rc_record, get_redcap_structure, get_code_by_name
from trd_cli.parse_tc import parse_tc


class ConversionsTest(TestCase):
    def setUp(self):
        self.expectations = {
            "phq9": {
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
            "gad7": {
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
            "mania": {
                "mania_response_id": "976453020",
                "mania_1_happiness_float": "1.0",
                "mania_2_confidence_float": "1.0",
                "mania_3_sleep_float": "1.0",
                "mania_4_talking_float": "1.0",
                "mania_5_activity_float": "2.0",
                "mania_datetime": "2024-11-05T12:05:59.3055890+00:00",
                "mania_score_total_float": "6.0",
            },
            "reqol10": {
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
                "reqol10_11_physical_health_float": "4.0",
                "reqol10_score_total_float": "24.0",
            },
            "wsas": {
                "wsas_response_id": "1212115884",
                "wsas_datetime": "2024-11-05T12:08:48.0135908+00:00",
                "wsas_1_work_float": "3.0",
                "wsas_2_management_float": "5.0",
                "wsas_3_social_leisure_float": "3.0",
                "wsas_4_private_leisure_float": "5.0",
                "wsas_5_family_float": "5.0",
                "wsas_score_total_float": "21.0",
            },
        }

    def test_convert_scores(self):
        responses = parse_tc("fixtures")
        self.assertIn("questionnaireresponse.csv", responses)
        done = []
        for r in responses["questionnaireresponse.csv"]:
            interop = r.get("interoperability")
            if interop is not None:
                q_title = interop.get("title")
                q_code = get_code_by_name(q_title)
                if q_code is not None and q_code not in done:
                    with self.subTest(q_name=q_code):
                        done.append(q_code)
                        if q_code not in self.expectations.keys():
                            if q_code == "consent":
                                continue
                            else:
                                self.fail(
                                    f"Unhandled questionnaire response of type {q_code}."
                                )
                        result = questionnaire_to_rc_record(r)
                        self.assertEqual(self.expectations[q_code], result)

        for q_code in self.expectations.keys():
            if q_code not in done:
                with self.subTest(q_name=q_code):
                    self.fail(f"Did not find a {q_code} row to test in data.")

    def test_extract_info(self):
        qr_file = "fixtures/patient.csv"
        with open(qr_file, "r") as f:
            responses = csv.DictReader(f, delimiter="|")
            response = next(responses)
        private, public = extract_participant_info(response)
        sleep(0.1)
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
                'info_is_test_bool': False,
            },
            public,
        )

    def test_redcap_dump(self):
        dump = get_redcap_structure()
        self.assertIn("private", dump)
        self.assertIsInstance(dump["private"], list)
        for f in ["id", "nhsnumber", "birthdate", "contactemail", "mobilenumber", "firstname", "lastname", "preferredcontact"]:
            self.assertIn(f, dump["private"])
        self.assertIn("info", dump)
        self.assertIsInstance(dump["info"], list)
        for f in ["info_birthyear_int", "info_datetime", "info_deceased_datetime", "info_gender_int", "info_is_deceased_bool", "info_is_test_bool"]:
            self.assertIn(f, dump["info"])
        for k, v in self.expectations.items():
            self.assertIn(k, dump)
            self.assertIsInstance(dump[k], list)
            for f in v.keys():
                self.assertIn(f, dump[k])


if __name__ == "__main__":
    main()
