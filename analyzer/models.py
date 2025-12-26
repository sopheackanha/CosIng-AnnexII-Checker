from django.db import models
from django.contrib.postgres.indexes import GinIndex

# Create your models here.
class ProhibitedIngredient(models.Model):
    """EU Annex II Prohibited substances"""
    name = models.TextField(db_index=True)
    name_normalized = models.TextField(db_index=True, help_text="Lowercase, trimmed version")
    cas_number = models.TextField(blank=True, null=True, db_index=True)
    ec_number = models.TextField(blank=True, null=True)
    regulation = models.TextField(blank=True, null=True)
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


class Analysis(models.Model):
    """Stored analysis runs for history and admin reporting."""

    STATUS_CHOICES = (
        ("safe", "Safe"),
        ("warning", "Warning"),
        ("prohibited", "Prohibited"),
    )

    INPUT_CHOICES = (
        ("text", "Text"),
        ("image", "Image"),
    )

    input_text = models.TextField()
    input_source = models.CharField(max_length=20, choices=INPUT_CHOICES, default="text")
    result_json = models.JSONField()
    overall_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="safe")

    total_ingredients = models.PositiveIntegerField(default=0)
    prohibited_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    safe_count = models.PositiveIntegerField(default=0)

    analysis_duration_ms = models.PositiveIntegerField(default=0)
    ip_address = models.CharField(max_length=64, blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Analysis #{self.id} ({self.overall_status})"

    def get_result_summary(self) -> str:
        return (
            f"{self.prohibited_count} prohibited, "
            f"{self.warning_count} warnings, "
            f"{self.safe_count} safe"
        )