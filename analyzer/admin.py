from django.contrib import admin
from django.utils.html import format_html
from .models import ProhibitedIngredient, Analysis

@admin.register(ProhibitedIngredient)
class ProhibitedIngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'cas_number', 'regulation', 'is_cmr', 'created_at']
    list_filter = ['is_cmr', 'created_at', 'regulation']
    search_fields = ['name', 'name_normalized', 'cas_number', 'regulation']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (
            'Basic Information',
            {'fields': ('name', 'name_normalized', 'cas_number', 'ec_number', 'regulation')},
        ),
        (
            'Classification',
            {'fields': ('is_cmr', 'cmr_note')},
        ),
        (
            'Metadata',
            {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)},
        ),
    )


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'created_at', 'status_badge', 'total_ingredients', 
        'prohibited_count', 'warning_count', 'input_preview', 'duration_display'
    ]
    list_filter = ['overall_status', 'input_source', 'created_at']
    search_fields = ['input_text', 'ip_address']
    readonly_fields = [
        'created_at', 'result_json', 'analysis_duration_ms',
        'ip_address', 'user_agent'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Input', {
            'fields': ('input_text', 'input_source')
        }),
        ('Results', {
            'fields': (
                'overall_status', 'result_json',
                'total_ingredients', 'prohibited_count', 
                'warning_count', 'safe_count'
            )
        }),
        ('Metadata', {
            'fields': (
                'ip_address', 'user_agent', 
                'analysis_duration_ms', 'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'safe': 'green',
            'warning': 'orange',
            'prohibited': 'red',
        }
        color = colors.get(obj.overall_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.overall_status.upper()
        )
    status_badge.short_description = 'Status'
    
    def input_preview(self, obj):
        return obj.input_text[:50] + '...' if len(obj.input_text) > 50 else obj.input_text
    input_preview.short_description = 'Input'
    
    def duration_display(self, obj):
        return f"{obj.analysis_duration_ms}ms"
    duration_display.short_description = 'Duration'
