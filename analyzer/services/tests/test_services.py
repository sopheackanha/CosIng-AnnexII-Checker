import os
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from analyzer.services.parser import IngredientParser
from analyzer.services.normalizer import IngredientNormalizer
from analyzer.services.matcher import IngredientMatcher
from analyzer.services.engine import IngredientAnalysisEngine

class ParserTestCase(TestCase):
    def setUp(self):
        self.parser = IngredientParser()
    
    def test_basic_parsing(self):
        text = "Water, Glycerin, Phenoxyethanol"
        result = self.parser.parse_ingredients(text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Water")
    
    def test_no_hyphen_splitting(self):
        text = "Butyl-Hydroxy-Toluene"
        result = self.parser.parse_ingredients(text)
        self.assertEqual(len(result), 1)
        self.assertIn("-", result[0])
    
    def test_empty_input(self):
        result = self.parser.parse_ingredients("")
        self.assertEqual(result, [])

class NormalizerTestCase(TestCase):
    def setUp(self):
        self.normalizer = IngredientNormalizer()
    
    def test_lowercase(self):
        result = self.normalizer.normalize("WATER")
        self.assertEqual(result, "water")
    
    def test_whitespace_strip(self):
        result = self.normalizer.normalize("  Glycerin  ")
        self.assertEqual(result, "glycerin")
    
    def test_canonical_mapping(self):
        result = self.normalizer.normalize("Aqua")
        self.assertEqual(result, "water")
    
    def test_safe_ingredient(self):
        self.assertTrue(self.normalizer.is_safe_ingredient("Water"))
        self.assertTrue(self.normalizer.is_safe_ingredient("Glycerin"))

class MatcherTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Load the real Annex II dataset into the test DB once
        csv_path = os.path.join(settings.BASE_DIR, "datasets", "COSING_Annex_II_v2.csv")
        call_command("load_annex_ii", csv_path, verbosity=0)

    def setUp(self):
        self.matcher = IngredientMatcher()
    
    def test_water_not_flagged(self):
        result = self.matcher.check_ingredient("Water")
        self.assertEqual(result['status'], "SAFE")
    
    def test_prohibited_ingredient_flagged(self):
        result = self.matcher.check_ingredient("Trichloroacetic acid")
        self.assertEqual(result['status'], "PROHIBITED")
        self.assertTrue(result['is_cmr'])
    
    def test_no_substring_false_positive(self):
        # "form" should NOT match "formaldehyde"
        result = self.matcher.check_ingredient("tric")
        self.assertEqual(result['status'], "SAFE")
    
    def test_fuzzy_match(self):
        result = self.matcher.check_ingredient("Trichloroacetic acd")  # Missing letters
        self.assertIn(result['status'], ["WARNING", "PROHIBITED"])
        self.assertGreaterEqual(result['confidence'], 90)

class EngineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        csv_path = os.path.join(settings.BASE_DIR, "datasets", "COSING_Annex_II_v2.csv")
        call_command("load_annex_ii", csv_path, verbosity=0)

    def setUp(self):
        self.engine = IngredientAnalysisEngine()
    
    def test_full_analysis(self):
        text = "Water, Glycerin, Trichloroacetic acid"
        result = self.engine.analyze(text)
        
        self.assertEqual(result['parsed_count'], 3)
        self.assertEqual(result['summary']['safe'], 2)
        self.assertEqual(result['summary']['prohibited'], 1)
