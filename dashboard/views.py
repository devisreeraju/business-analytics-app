from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datasets.models import Dataset
from analytics.models import DashboardState
from analytics.utils import generate_plotly_chart
from ai_advisor.models import AIReport
import pandas as pd
import numpy as np
import os

@login_required
def index(request):
    """
    Main dashboard page. Displays KPI cards, the active interactive chart,
    and a summary of the AI Business Advisor report.
    """
    user_datasets = Dataset.objects.filter(user=request.user)
    active_dataset = user_datasets.filter(is_active=True).first()
    
    if not active_dataset:
        return render(request, 'dashboard/index.html', {
            'active_dataset': None,
            'datasets_count': user_datasets.count()
        })
        
    # Read active dataset
    file_path = active_dataset.file.path
    if not os.path.exists(file_path):
        active_dataset.is_active = False
        active_dataset.save()
        return redirect('datasets:upload')
        
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return render(request, 'dashboard/index.html', {
            'active_dataset': active_dataset,
            'error_message': f"Failed to load active file: {str(e)}",
        })
        
    # Stats KPI calculations
    # Allow user to pick which numeric column to show stats (Mean, Max, Min) for
    stats_col = request.GET.get('stats_col')
    if not stats_col or stats_col not in active_dataset.numeric_columns:
        stats_col = active_dataset.numeric_columns[0] if active_dataset.numeric_columns else None
        
    stats_mean = None
    stats_max = None
    stats_min = None
    
    if stats_col and stats_col in df.columns:
        stats_mean = float(df[stats_col].mean())
        stats_max = float(df[stats_col].max())
        stats_min = float(df[stats_col].min())
        
    # Load dashboard chart state
    state, _ = DashboardState.objects.get_or_create(
        user=request.user,
        dataset=active_dataset,
        defaults={
            'chart_type': 'bar',
            'x_axis': active_dataset.categorical_columns[0] if active_dataset.categorical_columns else (active_dataset.numeric_columns[0] if active_dataset.numeric_columns else ''),
            'y_axis': active_dataset.numeric_columns[0] if active_dataset.numeric_columns else '',
            'filters': {}
        }
    )
    
    # Filter dataset for chart
    filtered_df = df.copy()
    for col, vals in state.filters.items():
        if vals and col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin(vals)]
            
    # Generate Plotly JSON
    theme = request.user.userprofile.theme_preference
    chart_json = generate_plotly_chart(
        filtered_df,
        state.chart_type,
        state.x_axis,
        state.y_axis,
        theme=theme
    )
    
    # Load AI report cache
    ai_report = AIReport.objects.filter(dataset=active_dataset).first()
    
    # Column metadata for KPI selection dropdown
    numeric_cols = active_dataset.numeric_columns
    
    return render(request, 'dashboard/index.html', {
        'active_dataset': active_dataset,
        'state': state,
        'chart_json': chart_json,
        'ai_report': ai_report,
        'stats_col': stats_col,
        'stats_mean': stats_mean,
        'stats_max': stats_max,
        'stats_min': stats_min,
        'numeric_cols': numeric_cols,
    })
