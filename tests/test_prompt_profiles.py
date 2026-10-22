import unittest
import json
from services.education.levels import Stage, EducationLevelCode, get_level
from services.education.prompt_profiles import get_prompt_profile
from services.qgen_service import build_prompt, generate_questions_from_content
from unittest.mock import patch, MagicMock


class TestPromptProfilesAndQgenIntegration(unittest.TestCase):
    def test_primary_1_prompt_calibration(self):
        """Primary 1 prompt must enforce primary language constraints, 3 choices, and primary examples."""
        p1_level = get_level("primary_1")
        prompt = build_prompt(
            text="Plants have roots and leaves.",
            refined_text="",
            description="",
            qtype="mcq",
            difficulty="easy",
            num_questions=3,
            education_level="primary_1"
        )
        self.assertIn("PRIMARY 1 / GRADE 1", prompt)
        self.assertIn("STAGE: PRIMARY", prompt)
        self.assertIn("Maximum options per question: 3", prompt)
        self.assertIn("concise (10-18 words max)", prompt)
        self.assertIn("What part of a plant takes in water from the soil?", prompt)
        self.assertNotIn("mitochondria", prompt.lower())

    def test_phd_prompt_calibration(self):
        """PhD prompt must enforce doctoral level critique and research methodology."""
        prompt = build_prompt(
            text="Empirical econometric analysis of institutional economics.",
            refined_text="",
            description="",
            qtype="mcq",
            difficulty="hard",
            num_questions=3,
            education_level="phd"
        )
        self.assertIn("DOCTORAL / PHD", prompt)
        self.assertIn("STAGE: DOCTORAL", prompt)
        self.assertIn("Scholarly peer-review standard", prompt)
        self.assertIn("regression discontinuity design", prompt)
        self.assertIn("McCrary density test", prompt)

    def test_backward_compatibility_with_class_id(self):
        """Passing class_id='Grade 5' automatically resolves to Primary 5."""
        prompt = build_prompt(
            text="General science concepts.",
            refined_text="",
            description="",
            qtype="mcq",
            difficulty="medium",
            class_id="Grade 5"
        )
        self.assertIn("Primary 5 / Grade 5", prompt)
        self.assertIn("primary_5", prompt)

    def test_choice_count_calibration_in_generated_questions(self):
        """Early Years and Primary 1-2 must enforce 3 choices max."""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps([
            {
                "question": "Which animal can fly?",
                "choices": ["Bird", "Fish", "Dog", "Cat"],
                "answer": "Bird",
                "rationale": "Birds have wings.",
                "qtype": "mcq",
                "difficulty": "easy",
                "blooms_level": "Remember"
            }
        ])
        mock_response.choices = [mock_choice]

        with patch("services.qgen_service.groq_client.chat.completions.create", return_value=mock_response):
            # Test Primary 1 (max 3 choices)
            res_str = generate_questions_from_content(
                text="Some text",
                num_questions=1,
                education_level="primary_1"
            )
            data = json.loads(res_str)
            self.assertEqual(len(data), 1)
            self.assertEqual(len(data[0]["choices"]), 3)
            self.assertEqual(data[0]["education_level"], "primary_1")

            # Test Senior Secondary 1 (max 4 choices)
            res_str_sss = generate_questions_from_content(
                text="Some text",
                num_questions=1,
                education_level="sss_1"
            )
            data_sss = json.loads(res_str_sss)
            self.assertEqual(len(data_sss[0]["choices"]), 4)
            self.assertEqual(data_sss[0]["education_level"], "sss_1")


if __name__ == "__main__":
    unittest.main()
