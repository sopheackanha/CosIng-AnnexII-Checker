from django import forms
from django.core.exceptions import ValidationError
import re

class IngredientAnalysisForm(forms.Form):
    """Form for text-based or image-based ingredient analysis"""
    
    ingredient_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Enter ingredients separated by commas, e.g.:\nWater, Glycerin, Phenoxyethanol, Sodium Laureth Sulfate',
            'maxlength': '10000'
        }),
        max_length=10000,
        required=False,
        label='Ingredient List',
    )
    
    image_file = forms.ImageField(
        required=False,
        label='Upload Image',
        help_text='Upload an image containing ingredients (JPG, PNG)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean(self):
        """Validate that either text or image is provided"""
        cleaned_data = super().clean()
        text = cleaned_data.get('ingredient_text')
        image = cleaned_data.get('image_file')
        
        # At least one input is required
        if not text and not image:
            raise ValidationError("Please provide either ingredient text or upload an image.")
        
        # Can't have both
        if text and image:
            raise ValidationError("Please provide either text or image, not both.")
        
        return cleaned_data
    
    def clean_ingredient_text(self):
        """Validate and sanitize ingredient text"""
        text = self.cleaned_data.get('ingredient_text', '')
        
        if not text:
            return text
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Check for empty input after strip
        if not text:
            return text
        
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
