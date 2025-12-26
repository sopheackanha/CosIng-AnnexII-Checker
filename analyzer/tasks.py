"""
Celery tasks for asynchronous processing.
"""
from celery import shared_task
from django.core.cache import cache
import logging
import time

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='analyzer.run_analysis_task')
def run_analysis_task(self, analysis_id: int, input_text: str, input_source: str = 'text'):
    """
    Asynchronously analyze ingredient text and store results.
    
    Args:
        analysis_id: ID of the Analysis model instance
        input_text: Text to analyze (from user input or OCR)
        input_source: Source of input ('text' or 'image')
        
    Returns:
        dict with analysis results
    """
    from analyzer.models import Analysis
    from analyzer.services.engine import analyze_text
    
    try:
        logger.info(f"Starting analysis task for Analysis #{analysis_id}")
        
        # Update task state to STARTED
        self.update_state(state='STARTED', meta={'status': 'Processing ingredients...'})
        
        # Start timing
        start_time = time.time()
        
        # Run analysis
        result = analyze_text(input_text)

        summary = result.get('summary', {}) or {}
        total_ingredients = result.get('parsed_count', 0)
        prohibited_count = summary.get('prohibited', 0)
        warning_count = summary.get('warnings', 0)
        safe_count = summary.get('safe', 0)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Determine overall status
        overall_status = 'safe'
        if prohibited_count > 0:
            overall_status = 'prohibited'
        elif warning_count > 0:
            overall_status = 'warning'
        
        # Update Analysis model
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.result_json = result
        analysis.overall_status = overall_status
        analysis.total_ingredients = total_ingredients
        analysis.prohibited_count = prohibited_count
        analysis.warning_count = warning_count
        analysis.safe_count = safe_count
        analysis.analysis_duration_ms = duration_ms
        analysis.save()
        
        logger.info(f"Analysis task completed for Analysis #{analysis_id} in {duration_ms}ms")
        
        return {
            'analysis_id': analysis_id,
            'status': 'completed',
            'overall_status': overall_status,
            'duration_ms': duration_ms,
            'result': result
        }
        
    except Analysis.DoesNotExist:
        logger.error(f"Analysis #{analysis_id} not found")
        raise
    except Exception as e:
        logger.error(f"Analysis task failed for Analysis #{analysis_id}: {str(e)}")
        # Update task state to FAILURE
        self.update_state(
            state='FAILURE',
            meta={'status': 'Analysis failed', 'error': str(e)}
        )
        raise


@shared_task(name='analyzer.cleanup_old_analyses')
def cleanup_old_analyses():
    """
    Periodic task to cleanup old analysis records.
    Keeps last 1000 analyses.
    """
    from analyzer.models import Analysis
    
    try:
        total_count = Analysis.objects.count()
        if total_count > 1000:
            # Get IDs of analyses to keep
            keep_ids = Analysis.objects.values_list('id', flat=True)[:1000]
            # Delete older ones
            deleted_count, _ = Analysis.objects.exclude(id__in=keep_ids).delete()
            logger.info(f"Cleaned up {deleted_count} old analysis records")
            return {'deleted': deleted_count}
        return {'deleted': 0}
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise
