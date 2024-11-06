import csv
import json
from unittest import TestCase, main

from trd_cli.types import (
    phq9_to_rc,
)


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
                    data = io
                    rc = phq9_to_rc(101, data)
                    self.assertEqual(
                        rc,
                        {
                            "study_id": 101,
                            "phq9_1_interest_int": "2",
                            "phq9_2_depression_int": "2",
                            "phq9_3_sleep_int": "2",
                            "phq9_4_lack_of_energy_int": "3",
                            "phq9_5_appetite_int": "2",
                            "phq9_6_view_of_self_int": "3",
                            "phq9_7_concentration_int": "2",
                            "phq9_8_movements_int": "1",
                            "phq9_9_self_harm_int": "3",
                            "phq9_score_total_int": "20",
                        },
                    )
                    return
        self.fail(f"No PHQ-9 questionnaire found in {qr_file}")


if __name__ == "__main__":
    main()
