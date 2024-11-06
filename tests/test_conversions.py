import csv
import json
from unittest import TestCase, main

from trd_cli.conversions import convert_questionnaire


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
                        convert_questionnaire(io),
                        {
                            "phq9_datetime": "2024-08-15T16:51:10.9141628+01:00",
                            "phq9_1_interest_float": "2.0",
                            "phq9_2_depression_float": "2.0",
                            "phq9_3_sleep_float": "2.0",
                            "phq9_4_lack_of_energy_float": "3.0",
                            "phq9_5_appetite_float": "2.0",
                            "phq9_6_view_of_self_float": "3.0",
                            "phq9_7_concentration_float": "2.0",
                            "phq9_8_movements_float": "1.0",
                            "phq9_9_self_harm_float": "3.0",
                            "phq9_score_total_float": "20.0",
                        },
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
                        convert_questionnaire(io),
                        {
                            "gad7_1_anxious_float": "2.0",
                            "gad7_2_uncontrollable_worrying_float": "2.0",
                            "gad7_3_excessive_worrying_float": "1.0",
                            "gad7_4_relaxing_float": "3.0",
                            "gad7_5_restless_float": "0.0",
                            "gad7_6_irritable_float": "1.0",
                            "gad7_7_afraid_float": "2.0",
                            "gad7_8_difficult_float": "0.0",
                            "gad7_datetime": "2024-08-09T11:45:33.1265670+01:00",
                            "gad7_score_total_float": "11.0"
                        },
                    )
                    return
        self.fail(f"No GAD-7 questionnaire found in {qr_file}")


if __name__ == "__main__":
    main()
