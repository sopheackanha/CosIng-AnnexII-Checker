from typing import List, Dict
from analyzer.services.parser import IngredientParser
from analyzer.services.normalizer import IngredientNormalizer
from analyzer.services.matcher import IngredientMatcher

class IngredientAnalysisEngine:
    """
    Main engine that coordinates parsing, normalization, and matching.
    """
    
    def __init__(self):
        self.parser = IngredientParser()
        self.normalizer = IngredientNormalizer()
        self.matcher = IngredientMatcher()
    
    def analyze(self, text: str) -> Dict:
        """
        Complete analysis pipeline.
        
        Args:
            text: Raw ingredient list
        
        Returns:
            {
                "input": original text,
                "parsed_count": int,
                "results": List[Dict],
                "summary": {
                    "prohibited": int,
                    "warnings": int,
                    "safe": int
                }
            }
        """
        # Parse
        ingredients = self.parser.parse_ingredients(text)
        
        # Match each ingredient
        results = self.matcher.check_batch(ingredients)
        
        # Calculate summary
        summary = {
            "prohibited": sum(1 for r in results if r['status'] == 'PROHIBITED'),
            "warnings": sum(1 for r in results if r['status'] == 'WARNING'),
            "safe": sum(1 for r in results if r['status'] == 'SAFE'),
        }
        
        return {
            "input": text,
            "parsed_count": len(ingredients),
            "results": results,
            "summary": summary
        }


# Shared, lightweight wrappers used by views/tests
_ENGINE = IngredientAnalysisEngine()


def analyze_text(text: str) -> Dict:
    """Convenience wrapper for text-based ingredient lists."""
    return _ENGINE.analyze(text or "")


def analyze_image(file_obj) -> Dict:
    """Placeholder image analyzer; extend with OCR if needed."""
    return {
        "input": "",
        "parsed_count": 0,
        "results": [],
        "summary": {"prohibited": 0, "warnings": 0, "safe": 0},
        "error": "analyze_image is not implemented"
    }


# Example usage
if __name__ == '__main__':
    engine = IngredientAnalysisEngine()
    
    test_text = "Water, Phenoxyethanol, Glycerin, Formaldehyde"
    result = engine.analyze(test_text)
    
    print("Analysis Results:")
    print(f"Parsed: {result['parsed_count']} ingredients")
    print(f"Summary: {result['summary']}")
    print("\nDetails:")
    for item in result['results']:
        print(f"  {item['ingredient']:30} → {item['status']} ({item['match_type']})")
