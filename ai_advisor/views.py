from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datasets.models import Dataset
from .models import AIReport
from .services import generate_ai_report_from_mistral
import datetime

@login_required
def view_report(request):
    """
    Renders the AI Business Advisor report panel. If no report is cached or
    if '?refresh=true' is passed, it queries the Mistral API and updates the cache.
    """
    user_datasets = Dataset.objects.filter(user=request.user)
    active_dataset = user_datasets.filter(is_active=True).first()
    
    if not active_dataset:
        return render(request, 'ai_advisor/view.html', {
            'active_dataset': None,
        })
        
    profile = request.user.userprofile
    api_key = profile.mistral_api_key
    
    # Check if API Key is configured
    if not api_key:
        return render(request, 'ai_advisor/view.html', {
            'active_dataset': active_dataset,
            'api_not_configured': True,
        })
        
    report = AIReport.objects.filter(dataset=active_dataset).first()
    refresh_requested = request.GET.get('refresh') == 'true'
    
    if not report or refresh_requested:
        # Trigger generation
        try:
            sections = generate_ai_report_from_mistral(active_dataset, api_key)
            
            # Delete older reports for this dataset
            AIReport.objects.filter(dataset=active_dataset).delete()
            
            # Save new report
            report = AIReport.objects.create(
                dataset=active_dataset,
                model_used='open-mistral-7b',
                executive_summary=sections['executive_summary'],
                business_highlights=sections['business_highlights'],
                risks=sections['risks'],
                opportunities=sections['opportunities'],
                recommendations=sections['recommendations'],
                conclusion=sections['conclusion']
            )
            
            # Reset profile unsaved changes since state is now saved
            profile.has_unsaved_changes = False
            profile.save()
            
            messages.success(request, "AI Business Report updated successfully!")
            return redirect('ai_advisor:view_report')
        except Exception as e:
            # If report fails, keep older cached report if exists, but warn user
            error_message = str(e)
            return render(request, 'ai_advisor/view.html', {
                'active_dataset': active_dataset,
                'report': report,
                'error_message': error_message,
            })
            
    return render(request, 'ai_advisor/view.html', {
        'active_dataset': active_dataset,
        'report': report,
    })


@login_required
def download_pdf(request):
    """
    Generates and downloads the current active AI report as a print-ready PDF file.
    """
    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()
    if not active_dataset:
        messages.error(request, "No active dataset found to download report.")
        return redirect('dashboard:index')
        
    report = AIReport.objects.filter(dataset=active_dataset).first()
    if not report:
        messages.error(request, "No AI report exists for the active dataset. Please generate it first.")
        return redirect('ai_advisor:view_report')
        
    # Render PDF template to HTML string
    html = render_to_string('ai_advisor/report_pdf.html', {
        'report': report,
        'dataset': active_dataset,
        'export_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user': request.user
    })
    
    # Create the HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="AI_Report_{active_dataset.name}.pdf"'
    
    # Compile HTML to PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"Error generating PDF: <pre>{html}</pre>")
        
    return response
