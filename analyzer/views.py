from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
import logging
import time

from .forms import IngredientAnalysisForm
from .models import Analysis
from .services.engine import IngredientAnalysisEngine

logger = logging.getLogger(__name__)

# Initialize analysis engine
engine = IngredientAnalysisEngine()


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Home page with ingredient input form.
    GET: Show form
    POST: Process analysis and redirect to results
    """
    if request.method == 'POST':
        form = IngredientAnalysisForm(request.POST)
        
        if form.is_valid():
            ingredient_text = form.cleaned_data['ingredient_text']
            
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
                
                # Get client info
                ip_address = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                
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
    
    context = {
        'form': form,
        'recent_count': recent_count,
    }
    
    return render(request, 'analyzer/analyzer.html', context)


def analysis_result(request, analysis_id):
    """
    Display results of a specific analysis.
    """
    analysis = get_object_or_404(Analysis, id=analysis_id)
    
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
    }
    
    return render(request, 'analyzer/results.html', context)


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
