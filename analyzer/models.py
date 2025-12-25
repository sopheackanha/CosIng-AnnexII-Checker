from django.db import models

# Create your models here.
class ProhibitedIngredient(models.Model):
    """EU Annex II Prohibited substances"""
    name = models.CharField(max_length=500, db_index=True)
    name_normalized = models.CharField(max_length=500, db_index=True, help_text="Lowercase, trimmed version")
    cas_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    annex_ref = models.CharField(max_length=200)
    is_cmr = models.BooleanField(default=False, help_text="Carcinogenic, Mutagenic, or Toxic for Reproduction")
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prohibited_ingredients'
        indexes = [
            models.Index(fields=['name_normalized']),
            models.Index(fields=['cas_number']),
        ]

    def __str__(self):
        return f"{self.name} ({self.annex_ref})"
    
# not yet make migration
# can make migration with command:
# python manage.py makemigrations
# python manage.py migrate