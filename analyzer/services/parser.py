import re
from typing import List

class IngredientParser:
    """
    Parse ingredient lists following strict rules:
    - Split ONLY by commas
    - No hyphen splitting
    - No substring splitting
    """
    
    @staticmethod
    def parse_ingredients(text: str) -> List[str]:
        """
        Parse ingredient text into individual ingredients.
        
        Args:
            text: Raw ingredient text (e.g., "Water, Glycerin, Sodium Laureth Sulfate")
        
        Returns:
            List of individual ingredients
        """
        if not text or not isinstance(text, str):
            return []
        
        # Split by comma
        ingredients = text.split(',')
        
        # Clean each ingredient
        cleaned = []
        for ingredient in ingredients:
            # Strip whitespace
            ingredient = ingredient.strip()
            
            # Skip empty strings
            if not ingredient:
                continue
            
            # Remove parenthetical content (optional - adjust based on needs)
            # e.g., "Glycerin (Vegetable)" → "Glycerin"
            # ingredient = re.sub(r'\([^)]*\)', '', ingredient).strip()
            
            cleaned.append(ingredient)
        
        return cleaned
    
    @staticmethod
    def parse_with_metadata(text: str) -> List[dict]:
        """
        Parse ingredients with position metadata for highlighting.
        
        Returns:
            List of dicts with 'name', 'position', 'original'
        """
        ingredients = []
        parts = text.split(',')
        position = 0
        
        for i, part in enumerate(parts):
            stripped = part.strip()
            if stripped:
                ingredients.append({
                    'name': stripped,
                    'position': i,
                    'original': part,
                })
        
        return ingredients


# Example
if __name__ == '__main__':
    parser = IngredientParser()
    
    test_cases = [
        "Water, Phenoxyethanol, Sodium Laureth Sulfate",
        "Aqua, Glycerin, Butyl-Hydroxy-Toluene",
        "Water,Glycerin,  Preservative  ",
    ]
    
    for test in test_cases:
        result = parser.parse_ingredients(test)
        print(f"Input: {test}")
        print(f"Output: {result}\n")
