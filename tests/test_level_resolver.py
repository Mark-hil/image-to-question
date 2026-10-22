import unittest
from services.education.resolver import resolve_level, resolve_level_and_label
from services.education.levels import EducationLevelCode


class TestLevelResolver(unittest.TestCase):
    def test_direct_canonical_codes(self):
        """Canonical codes resolve directly."""
        lvl = resolve_level("primary_1")
        self.assertIsNotNone(lvl)
        self.assertEqual(lvl.code, EducationLevelCode.PRIMARY_1.value)

        lvl_phd = resolve_level("phd")
        self.assertIsNotNone(lvl_phd)
        self.assertEqual(lvl_phd.code, EducationLevelCode.PHD.value)

    def test_grade_and_class_patterns(self):
        """Patterns like Grade 5, Class 5A, Basic 3, Year 10."""
        cases = [
            ("Grade 1", EducationLevelCode.PRIMARY_1.value),
            ("grade 5", EducationLevelCode.PRIMARY_5.value),
            ("Class 5A", EducationLevelCode.PRIMARY_5.value),
            ("Basic 3", EducationLevelCode.PRIMARY_3.value),
            ("P4", EducationLevelCode.PRIMARY_4.value),
            ("Grade 7", EducationLevelCode.JSS_1.value),
            ("Grade 8", EducationLevelCode.JSS_2.value),
            ("Grade 9", EducationLevelCode.JSS_3.value),
            ("Grade 10", EducationLevelCode.SSS_1.value),
            ("Grade 11", EducationLevelCode.SSS_2.value),
            ("Grade 12", EducationLevelCode.SSS_3.value),
            ("Year 11", EducationLevelCode.SSS_2.value),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw, expected=expected):
                resolved = resolve_level(raw)
                self.assertIsNotNone(resolved, f"Failed to resolve {raw}")
                self.assertEqual(resolved.code, expected)

    def test_jhs_shs_and_west_african_aliases(self):
        """JHS 1-3, SHS 1-3, WASSCE, BECE."""
        cases = [
            ("JHS 1", EducationLevelCode.JSS_1.value),
            ("JSS 2", EducationLevelCode.JSS_2.value),
            ("BECE", EducationLevelCode.JSS_3.value),
            ("SHS 1", EducationLevelCode.SSS_1.value),
            ("SSS 3", EducationLevelCode.SSS_3.value),
            ("WASSCE", EducationLevelCode.SSS_3.value),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw, expected=expected):
                resolved = resolve_level(raw)
                self.assertIsNotNone(resolved, f"Failed to resolve {raw}")
                self.assertEqual(resolved.code, expected)

    def test_tertiary_and_postgraduate_aliases(self):
        """Undergraduate levels (100-400), Masters, PhD."""
        cases = [
            ("Level 100", EducationLevelCode.UG_1.value),
            ("200 level", EducationLevelCode.UG_2.value),
            ("Level 300", EducationLevelCode.UG_3.value),
            ("400L", EducationLevelCode.UG_4.value),
            ("College Freshman", EducationLevelCode.UG_1.value),
            ("Undergraduate", EducationLevelCode.UG_4.value),
            ("Masters", EducationLevelCode.MASTERS.value),
            ("MSc", EducationLevelCode.MASTERS.value),
            ("MBA", EducationLevelCode.MASTERS.value),
            ("PhD", EducationLevelCode.PHD.value),
            ("Ph.D.", EducationLevelCode.PHD.value),
            ("Doctorate", EducationLevelCode.PHD.value),
            ("Postdoc", EducationLevelCode.POSTDOC.value),
            ("CPA", EducationLevelCode.PROFESSIONAL.value),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw, expected=expected):
                resolved = resolve_level(raw)
                self.assertIsNotNone(resolved, f"Failed to resolve {raw}")
                self.assertEqual(resolved.code, expected)

    def test_diploma_and_polytechnic_aliases(self):
        """Diploma, ND 1-2, HND, Polytechnic, TVET."""
        cases = [
            ("Diploma", EducationLevelCode.DIPLOMA_1.value),
            ("deploma", EducationLevelCode.DIPLOMA_1.value),
            ("National Diploma", EducationLevelCode.DIPLOMA_1.value),
            ("ND 1", EducationLevelCode.DIPLOMA_1.value),
            ("Diploma 1", EducationLevelCode.DIPLOMA_1.value),
            ("ND 2", EducationLevelCode.DIPLOMA_2.value),
            ("Diploma 2", EducationLevelCode.DIPLOMA_2.value),
            ("HND", EducationLevelCode.ADVANCED_DIPLOMA.value),
            ("HND 1", EducationLevelCode.ADVANCED_DIPLOMA.value),
            ("Higher National Diploma", EducationLevelCode.ADVANCED_DIPLOMA.value),
            ("Polytechnic Diploma", EducationLevelCode.DIPLOMA_1.value),
            ("TVET", EducationLevelCode.DIPLOMA_1.value),
            ("Associate Degree", EducationLevelCode.DIPLOMA_1.value),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw, expected=expected):
                resolved = resolve_level(raw)
                self.assertIsNotNone(resolved, f"Failed to resolve {raw}")
                self.assertEqual(resolved.code, expected)

    def test_numeric_only_strings(self):
        """When user provides just a number like '5' or '10'."""
        self.assertEqual(resolve_level("1").code, EducationLevelCode.PRIMARY_1.value)
        self.assertEqual(resolve_level("5").code, EducationLevelCode.PRIMARY_5.value)
        self.assertEqual(resolve_level("8").code, EducationLevelCode.JSS_2.value)
        self.assertEqual(resolve_level("10").code, EducationLevelCode.SSS_1.value)

    def test_resolve_level_and_label(self):
        """Extracts level while keeping class label intact."""
        lvl, label = resolve_level_and_label("Class 5B")
        self.assertEqual(lvl.code, EducationLevelCode.PRIMARY_5.value)
        self.assertEqual(label, "Class 5B")

        lvl2, label2 = resolve_level_and_label(None)
        self.assertIsNone(lvl2)
        self.assertIsNone(label2)


if __name__ == "__main__":
    unittest.main()
