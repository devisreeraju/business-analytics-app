from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datasets.models import Dataset
from ai_advisor.models import AIReport
from analytics.models import DashboardState
import pandas as pd
import numpy as np
import io
import zipfile
import datetime
import os

@login_required
def index(request):
    """
    Renders the Export Module workspace where users can choose to export
    the dashboard layout, dataset tables, or a consolidated ZIP file.
    """
    user_datasets = Dataset.objects.filter(user=request.user)
    active_dataset = user_datasets.filter(is_active=True).first()
    
    return render(request, 'export/index.html', {
        'active_dataset': active_dataset,
    })


@login_required
def export_dataset_csv(request):
    """
    Reads the active dataset and triggers a browser download as a CSV file.
    """
    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()
    if not active_dataset:
        messages.error(request, "No active dataset found to export.")
        return redirect('export:index')
        
    file_path = active_dataset.file.path
    if not os.path.exists(file_path):
        messages.error(request, "Dataset file not found on disk.")
        return redirect('export:index')
        
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{active_dataset.name}.csv"'
        df.to_csv(path_or_buf=response, index=False)
        return response
    except Exception as e:
        messages.error(request, f"Error generating CSV export: {str(e)}")
        return redirect('export:index')


@login_required
def export_dataset_excel(request):
    """
    Reads the active dataset and triggers a browser download as an Excel (.xlsx) file.
    """
    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()
    if not active_dataset:
        messages.error(request, "No active dataset found to export.")
        return redirect('export:index')
        
    file_path = active_dataset.file.path
    if not os.path.exists(file_path):
        messages.error(request, "Dataset file not found on disk.")
        return redirect('export:index')
        
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Write to response using Pandas
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{active_dataset.name}.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            
        return response
    except Exception as e:
        messages.error(request, f"Error generating Excel export: {str(e)}")
        return redirect('export:index')


@login_required
def export_complete_zip(request):
    """
    Compiles and downloads a ZIP file containing the original dataset,
    the AI advisor report PDF, and the dashboard summary report PDF.
    """
    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()
    if not active_dataset:
        messages.error(request, "No active dataset found to export.")
        return redirect('export:index')
        
    # Check if AI report exists. If not, generate a dummy or warn user.
    ai_report = AIReport.objects.filter(dataset=active_dataset).first()
    if not ai_report:
        messages.warning(request, "Please generate the AI report first before exporting the complete bundle.")
        return redirect('ai_advisor:view_report')
        
    try:
        # Create an in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Add Original Dataset file
            dataset_path = active_dataset.file.path
            dataset_name = os.path.basename(active_dataset.file.name)
            zip_file.write(dataset_path, f"data/{dataset_name}")
            
            # 2. Add AI Report PDF
            ai_html = render_to_string('ai_advisor/report_pdf.html', {
                'report': ai_report,
                'dataset': active_dataset,
                'export_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': request.user
            })
            ai_pdf_buffer = io.BytesIO()
            pisa.CreatePDF(ai_html, dest=ai_pdf_buffer)
            zip_file.writestr(f"reports/AI_Advisor_Report_{active_dataset.name}.pdf", ai_pdf_buffer.getvalue())
            
            # 3. Add Dashboard PDF report (backend compilation of KPI, axes, and details)
            # Fetch numeric summary stats
            stats_summary = {}
            try:
                if dataset_path.endswith('.csv'):
                    df = pd.read_csv(dataset_path)
                else:
                    df = pd.read_excel(dataset_path)
                for col in active_dataset.numeric_columns:
                    stats_summary[col] = {
                        'mean': float(df[col].mean()),
                        'max': float(df[col].max()),
                        'min': float(df[col].min())
                    }
            except Exception:
                stats_summary = {}
                
            dash_state = DashboardState.objects.filter(user=request.user, dataset=active_dataset).first()
            
            dash_html = render_to_string('export/dashboard_pdf.html', {
                'dataset': active_dataset,
                'state': dash_state,
                'stats_summary': stats_summary,
                'export_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user': request.user
            })
            dash_pdf_buffer = io.BytesIO()
            pisa.CreatePDF(dash_html, dest=dash_pdf_buffer)
            zip_file.writestr(f"reports/Dashboard_Summary_{active_dataset.name}.pdf", dash_pdf_buffer.getvalue())
            
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="Complete_Report_Bundle_{active_dataset.name}.zip"'
        return response
    except Exception as e:
        messages.error(request, f"Failed to generate consolidated ZIP: {str(e)}")
        return redirect('export:index')
