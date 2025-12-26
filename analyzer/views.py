from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from celery.result import AsyncResult
import logging
import time
import os

from .forms import IngredientAnalysisForm
from .models import Analysis
from .services.engine import IngredientAnalysisEngine
from .services.ocr import extract_text_from_image, OCRError, is_tesseract_available
from .tasks import run_analysis_task

logger = logging.getLogger(__name__)

# Initialize analysis engine
engine = IngredientAnalysisEngine()


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Home page with ingredient input form.
    GET: Show form
    POST: Process analysis (sync for text, async for images) and redirect to results
    """
    if request.method == 'POST':
        form = IngredientAnalysisForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Check if image upload or text input
            image_file = request.FILES.get('image_file')
            ingredient_text = form.cleaned_data.get('ingredient_text', '')
            
            # Get client info
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            if image_file:
                # Handle image upload with async processing
                try:
                    # Check if Tesseract is available
                    if not is_tesseract_available():
                        messages.error(
                            request,
                            "OCR service is not available. Please install Tesseract or use text input."
                        )
                        return render(request, 'analyzer/analyzer.html', {'form': form})
                    
                    # Save uploaded image
                    file_path = default_storage.save(
                        f'uploads/{image_file.name}',
                        image_file
                    )
                    full_path = default_storage.path(file_path)
                    
                    # Extract text using OCR
                    try:
                        extracted_text = extract_text_from_image(full_path)
                        if not extracted_text:
                            messages.error(request, "No text could be extracted from the image. Please try again.")
                            default_storage.delete(file_path)
                            return render(request, 'analyzer/analyzer.html', {'form': form})
                    except OCRError as e:
                        messages.error(request, f"OCR failed: {str(e)}")
                        default_storage.delete(file_path)
                        return render(request, 'analyzer/analyzer.html', {'form': form})
                    finally:
                        # Clean up uploaded file
                        if os.path.exists(full_path):
                            default_storage.delete(file_path)
                    
                    # Create Analysis record
                    analysis = Analysis.objects.create(
                        input_text=extracted_text,
                        input_source='image',
                        result_json={},
                        overall_status='safe',
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    
                    # Trigger async task
                    task = run_analysis_task.delay(
                        analysis.id,
                        extracted_text,
                        'image'
                    )
                    
                    logger.info(f"Started async analysis task {task.id} for Analysis #{analysis.id}")
                    
                    # Redirect to results page (will show loading state)
                    return redirect('analysis_result', analysis_id=analysis.id)
                    
                except Exception as e:
                    logger.error(f"Image upload failed: {str(e)}", exc_info=True)
                    messages.error(request, "Image processing failed. Please try again.")
                    return render(request, 'analyzer/analyzer.html', {'form': form})
            
            else:
                # Handle text input synchronously (existing logic)
                # Start timing
                start_time = time.time()
                
                try:
                    # Run analysis
                    result = engine.analyze(ingredient_text)
                    
                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    # Determine overall status
                    if result['summary']['prohibited'] > 0:
                        overall_status = 'prohibited'
                    elif result['summary']['warnings'] > 0:
                        overall_status = 'warning'
                    else:
                        overall_status = 'safe'
                    
                    # Save to database
                    analysis = Analysis.objects.create(
                        input_text=ingredient_text,
                        input_source='text',
                        result_json=result,
                        overall_status=overall_status,
                        total_ingredients=result['parsed_count'],
                        prohibited_count=result['summary']['prohibited'],
                        warning_count=result['summary']['warnings'],
                        safe_count=result['summary']['safe'],
                        ip_address=ip_address,
                        user_agent=user_agent,
                        analysis_duration_ms=duration_ms
                    )
                    
                    logger.info(f"Analysis #{analysis.id} completed in {duration_ms}ms - Status: {overall_status}")
                    
                    # Redirect to results page
                    return redirect('analysis_result', analysis_id=analysis.id)
                    
                except Exception as e:
                    logger.error(f"Analysis failed: {str(e)}", exc_info=True)
                    messages.error(request, "An error occurred during analysis. Please try again.")
                    form = IngredientAnalysisForm()
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = IngredientAnalysisForm()
    
    # Get recent analyses count
    recent_count = Analysis.objects.count()
    
    # Check OCR availability
    ocr_available = is_tesseract_available()
    
    context = {
        'form': form,
        'recent_count': recent_count,
        'ocr_available': ocr_available,
    }
    
    return render(request, 'analyzer/analyzer.html', context)


def analysis_result(request, analysis_id):
    """
    Display results of a specific analysis.
    For async tasks, polls for completion.
    """
    analysis = get_object_or_404(Analysis, id=analysis_id)
    
    # Check if analysis is complete
    is_pending = not analysis.result_json or analysis.result_json == {}
    
    if is_pending:
        # Analysis is still processing (async task)
        context = {
            'analysis': analysis,
            'is_pending': True,
        }
        return render(request, 'analyzer/results.html', context)
    
    # Extract results
    result_data = analysis.result_json
    results = result_data.get('results', [])
    summary = result_data.get('summary', {})
    
    # Separate ingredients by status
    prohibited = [r for r in results if r['status'] == 'PROHIBITED']
    warnings = [r for r in results if r['status'] == 'WARNING']
    safe = [r for r in results if r['status'] == 'SAFE']
    
    context = {
        'analysis': analysis,
        'results': results,
        'summary': summary,
        'prohibited': prohibited,
        'warnings': warnings,
        'safe': safe,
        'is_pending': False,
    }
    
    return render(request, 'analyzer/results.html', context)


@require_http_methods(["GET"])
def check_analysis_status(request, analysis_id):
    """
    API endpoint to check if async analysis is complete.
    Returns JSON with status.
    """
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        
        # Check if result is populated
        is_complete = analysis.result_json and analysis.result_json != {}
        
        response = {
            'complete': is_complete,
            'status': analysis.overall_status,
        }
        
        if is_complete:
            response['redirect_url'] = f'/analysis/{analysis_id}/'
        
        return JsonResponse(response)
        
    except Analysis.DoesNotExist:
        return JsonResponse({'error': 'Analysis not found'}, status=404)


def history(request):
    """
    Display history of all analyses with pagination.
    """
    # Get all analyses, ordered by most recent
    analyses_list = Analysis.objects.all().order_by('-created_at')
    
    # Pagination (10 per page)
    paginator = Paginator(analyses_list, 10)
    page_number = request.GET.get('page')
    analyses = paginator.get_page(page_number)
    
    # Calculate statistics
    total_analyses = Analysis.objects.count()
    total_prohibited = Analysis.objects.filter(overall_status='prohibited').count()
    total_warnings = Analysis.objects.filter(overall_status='warning').count()
    total_safe = Analysis.objects.filter(overall_status='safe').count()
    
    context = {
        'analyses': analyses,
        'total_analyses': total_analyses,
        'total_prohibited': total_prohibited,
        'total_warnings': total_warnings,
        'total_safe': total_safe,
    }
    
    return render(request, 'analyzer/history.html', context)


def delete_analysis(request, analysis_id):
    """
    Delete a specific analysis (optional feature).
    """
    if request.method == 'POST':
        analysis = get_object_or_404(Analysis, id=analysis_id)
        analysis.delete()
        messages.success(request, "Analysis deleted successfully.")
        logger.info(f"Analysis #{analysis_id} deleted")
    
    return redirect('history')


# Helper function
def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
