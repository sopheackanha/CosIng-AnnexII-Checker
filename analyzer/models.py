from django.db import models
from django.contrib.postgres.indexes import GinIndex

# Create your models here.
class ProhibitedIngredient(models.Model):
    """EU Annex II Prohibited substances"""
    name = models.TextField(db_index=True)
    name_normalized = models.TextField(db_index=True, help_text="Lowercase, trimmed version")
    cas_number = models.CharField(blank=True, null=True, db_index=True)
    ec_number = models.CharField(blank=True, null=True)
    regulation = models.CharField(blank=True, null=True)
    is_cmr = models.BooleanField(default=False, help_text="Carcinogenic, Mutagenic, or Toxic for Reproduction")
    cmr_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # define metadata of the model
    class Meta:
        db_table = 'prohibited_ingredients'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['name_normalized']),
            models.Index(fields=['cas_number']),
            GinIndex(fields=['name'], name='name_gin_trgm', opclasses=['gin_trgm_ops']), #for partial or fuzzy match when search
        ]

    def __str__(self):
        return f"{self.name}"
    
# not yet make migration
# can make migration with command:
# python manage.py makemigrations
# python manage.py migrate