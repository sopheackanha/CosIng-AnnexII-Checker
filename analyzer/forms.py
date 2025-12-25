from django import forms
from django.core.exceptions import ValidationError
import re

class IngredientAnalysisForm(forms.Form):
    """Form for text-based ingredient analysis"""
    
    ingredient_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Enter ingredients separated by commas, e.g.:\nWater, Glycerin, Phenoxyethanol, Sodium Laureth Sulfate',
            'maxlength': '10000'
        }),
        max_length=10000,
        required=True,
        label='Ingredient List',
        help_text='Paste your ingredient list here (separated by commas)'
    )
    
    def clean_ingredient_text(self):
        """Validate and sanitize ingredient text"""
        text = self.cleaned_data.get('ingredient_text', '')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Check for empty input
        if not text:
            raise ValidationError("Please enter at least one ingredient.")
        
        # Check minimum length (at least one character after comma split)
        if len(text) < 2:
            raise ValidationError("Input is too short. Please enter valid ingredients.")
        
        # Reject HTML/script tags
        html_pattern = re.compile(r'<[^>]+>')
        if html_pattern.search(text):
            raise ValidationError("HTML tags are not allowed.")
        
        # Reject script content
        script_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
        ]
        for pattern in script_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValidationError("Invalid content detected.")
        
        # Check for at least one comma or word
        if ',' not in text and len(text.split()) == 0:
            raise ValidationError("Please enter ingredients separated by commas.")
        
        return text
