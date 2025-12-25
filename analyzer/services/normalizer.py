from typing import Dict, Optional

class IngredientNormalizer:
    """
    Normalize ingredient names for consistent matching.
    Rules:
    - Lowercase
    - Strip whitespace
    - Canonical mapping (INCI → common names)
    - NO stemming
    - NO hyphen removal
    """
    
    # Canonical mapping (INCI name → normalized)
    CANONICAL_MAP = {
        'aqua': 'water',
        'tocopherol': 'vitamin e',
        'ascorbic acid': 'vitamin c',
        'retinol': 'vitamin a',
        'sodium chloride': 'salt',
        # Add more as needed
    }
    
    # Safe ingredients (never flag)
    SAFE_INGREDIENTS = {
        'water', 'aqua', 'glycerin', 'glycerol',
        'salt', 'sodium chloride', 'sugar',
        'stearic acid', 'citric acid'
    }
    
    @staticmethod
    def normalize(ingredient: str) -> str:
        """
        Normalize an ingredient name.
        
        Args:
            ingredient: Raw ingredient name
        
        Returns:
            Normalized ingredient name
        """
        if not ingredient:
            return ''
        
        # Lowercase
        normalized = ingredient.lower()
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        # Canonical mapping
        normalized = IngredientNormalizer.CANONICAL_MAP.get(
            normalized, normalized
        )
        
        return normalized
    
    @staticmethod
    def is_safe_ingredient(ingredient: str) -> bool:
        """
        Check if ingredient is in safe list.
        """
        normalized = IngredientNormalizer.normalize(ingredient)
        return normalized in IngredientNormalizer.SAFE_INGREDIENTS
    
    @staticmethod
    def normalize_batch(ingredients: list) -> list:
        """
        Normalize a batch of ingredients.
        """
        return [
            IngredientNormalizer.normalize(ing) 
            for ing in ingredients
        ]


# Example usage
if __name__ == '__main__':
    normalizer = IngredientNormalizer()
    
    tests = [
        "Water",
        "AQUA",
        "  Glycerin  ",
        "Sodium Laureth Sulfate",
        "Butyl-Hydroxy-Toluene",
    ]
    
    for test in tests:
        normalized = normalizer.normalize(test)
        is_safe = normalizer.is_safe_ingredient(test)
        print(f"{test:30} → {normalized:30} [Safe: {is_safe}]")
