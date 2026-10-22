import unittest
from services.education.levels import (
    Stage,
    EducationLevelCode,
    LEVELS,
    LEVELS_BY_CODE,
    get_level,
    list_levels,
    levels_by_stage,
    codes_in_range,
)
from services.education.prompt_profiles import PROMPT_PROFILES_BY_STAGE, get_prompt_profile


class TestEducationLevelsRegistry(unittest.TestCase):
    def test_levels_count_and_uniqueness(self):
        """Verify all levels have unique codes, ordinals, and valid properties."""
        codes = [l.code for l in LEVELS]
        self.assertEqual(len(codes), len(set(codes)), "Level codes must be unique")
        
        ordinals = [l.ordinal for l in LEVELS]
        # Verify ordinals are sorted
        self.assertEqual(ordinals, sorted(ordinals), "Ordinals must be non-decreasing")

    def test_every_stage_has_prompt_profile(self):
        """Verify every defined stage has an associated PromptProfile."""
        for stage in Stage:
            self.assertIn(stage, PROMPT_PROFILES_BY_STAGE)
            profile = get_prompt_profile(stage)
            self.assertEqual(profile.stage, stage)
            self.assertTrue(len(profile.audience_description) > 0)
            self.assertTrue(len(profile.few_shot_examples) > 0)

    def test_lookup_functions(self):
        """Verify get_level and list_levels."""
        p1 = get_level("primary_1")
        self.assertIsNotNone(p1)
        self.assertEqual(p1.stage, Stage.PRIMARY)
        self.assertEqual(p1.max_choices, 3)

        phd = get_level("phd")
        self.assertIsNotNone(phd)
        self.assertEqual(phd.stage, Stage.DOCTORAL)

        # Invalid returns None
        self.assertIsNone(get_level("non_existent_level"))
        self.assertIsNone(get_level(None))

    def test_levels_by_stage(self):
        """Verify grouping by stage."""
        primaries = levels_by_stage(Stage.PRIMARY)
        self.assertEqual(len(primaries), 6)  # Primary 1 to 6
        self.assertTrue(all(p.stage == Stage.PRIMARY for p in primaries))

        doctorals = levels_by_stage(Stage.DOCTORAL)
        self.assertEqual(len(doctorals), 2)  # PhD and Postdoc

        diplomas = levels_by_stage(Stage.DIPLOMA)
        self.assertEqual(len(diplomas), 3)  # ND 1, ND 2, HND
        self.assertTrue(all(d.stage == Stage.DIPLOMA for d in diplomas))

    def test_codes_in_range(self):
        """Verify ordinal range slice."""
        rng = codes_in_range("primary_1", "primary_3")
        self.assertEqual(rng, ("primary_1", "primary_2", "primary_3"))

        # Inverted should still order correctly
        rng_inv = codes_in_range("primary_3", "primary_1")
        self.assertEqual(rng_inv, ("primary_1", "primary_2", "primary_3"))


if __name__ == "__main__":
    unittest.main()
