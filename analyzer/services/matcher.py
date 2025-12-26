from typing import Optional, Dict, List
from rapidfuzz import fuzz
from django.core.cache import cache
from analyzer.models import ProhibitedIngredient
from analyzer.services.normalizer import IngredientNormalizer
import logging

logger = logging.getLogger(__name__)


class IngredientMatcher:
    """
    Match ingredients against Annex II prohibited list.
    Priority:
    1. Exact match
    2. Fuzzy match (≥90% similarity)
    3. Safe override (never flag safe ingredients)
    
    Uses Redis caching to optimize performance.
    """
    
    FUZZY_THRESHOLD = 90
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
    
    def __init__(self):
        self.normalizer = IngredientNormalizer()
        # Cache prohibited ingredients for performance
        self._cache = None
    
    def _load_cache(self):
        """Load all prohibited ingredients into memory with Redis caching."""
        cache_key = 'prohibited_ingredients_list_v2'
        
        # Try to get from Redis cache first
        self._cache = cache.get(cache_key)
        
        if self._cache is None:
            logger.info("Loading prohibited ingredients from database")
            self._cache = list(
                ProhibitedIngredient.objects.all().values(
                    'name', 'name_normalized', 'cas_number',
                    'regulation', 'is_cmr', 'cmr_note'
                )
            )
            # Store in Redis cache
            cache.set(cache_key, self._cache, self.CACHE_TIMEOUT)
            logger.info(f"Cached {len(self._cache)} prohibited ingredients")
        else:
            logger.debug("Using cached prohibited ingredients list")

    
    def check_ingredient(self, ingredient: str) -> Dict:
        """
        Check a single ingredient against Annex II with caching.
        
        Returns:
            {
                "ingredient": "original name",
                "status": "SAFE" | "PROHIBITED" | "WARNING",
                "match_type": "exact" | "fuzzy" | "none",
                "regulation": "(EC) 2009/1223" | None,
                "is_cmr": bool,
                "cmr_note": str | None,
                "confidence": 0-100,
                "matched_name": "official name if matched"
            }
        """
        # Check individual ingredient cache first
        cache_key = f'ingredient_check:v2:{ingredient.lower()}'
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for ingredient: {ingredient}")
            return cached_result
        
        self._load_cache()
        
        # Normalize
        normalized = self.normalizer.normalize(ingredient)
        
        # Safe override
        if self.normalizer.is_safe_ingredient(ingredient):
            result = {
                "ingredient": ingredient,
                "status": "SAFE",
                "match_type": "safe_list",
                "confidence": 100,
                "regulation": None,
                "is_cmr": False,
                "cmr_note": None,
                "matched_name": None
            }
            cache.set(cache_key, result, self.CACHE_TIMEOUT)
            return result
        
        # 1. Try exact match
        exact_match = self._exact_match(normalized)
        if exact_match:
            cache.set(cache_key, exact_match, self.CACHE_TIMEOUT)
            return exact_match
        
        # 2. Try fuzzy match
        fuzzy_match = self._fuzzy_match(normalized)
        if fuzzy_match:
            cache.set(cache_key, fuzzy_match, self.CACHE_TIMEOUT)
            return fuzzy_match
        
        # 3. No match found
        result = {
            "ingredient": ingredient,
            "status": "SAFE",
            "match_type": "none",
            "confidence": 100,
            "regulation": None,
            "is_cmr": False,
            "cmr_note": None,
            "matched_name": None
        }
        
        # Cache the result
        cache.set(cache_key, result, self.CACHE_TIMEOUT)
        return result
    
    def _exact_match(self, normalized: str) -> Optional[Dict]:
        """Check for exact match."""
        for item in self._cache:
            if item['name_normalized'] == normalized:
                return {
                    "ingredient": normalized,
                    "status": "PROHIBITED",
                    "match_type": "exact",
                    "confidence": 100,
                    "regulation": item['regulation'],
                    "is_cmr": item['is_cmr'],
                    "cmr_note": item.get('cmr_note'),
                    "matched_name": item['name']
                }
        return None
    
    def _fuzzy_match(self, normalized: str) -> Optional[Dict]:
        """Check for fuzzy match."""
        best_match = None
        best_score = 0
        
        for item in self._cache:
            score = fuzz.ratio(normalized, item['name_normalized'])
            if score >= self.FUZZY_THRESHOLD and score > best_score:
                best_score = score
                best_match = item
        
        if best_match:
            return {
                "ingredient": normalized,
                "status": "WARNING" if best_score < 98 else "PROHIBITED",
                "match_type": "fuzzy",
                "confidence": best_score,
                "regulation": best_match['regulation'],
                "is_cmr": best_match['is_cmr'],
                "cmr_note": best_match.get('cmr_note'),
                "matched_name": best_match['name']
            }
        
        return None
    
    def check_batch(self, ingredients: List[str]) -> List[Dict]:
        """Check multiple ingredients."""
        return [self.check_ingredient(ing) for ing in ingredients]
