from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Dataset
from .forms import DatasetUploadForm
import pandas as pd
import numpy as np
import os

@login_required
def upload_view(request):
    user_datasets = Dataset.objects.filter(user=request.user)
    active_dataset = user_datasets.filter(is_active=True).first()
    
    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.user = request.user
            # Extract name from filename without extension
            dataset.name = os.path.splitext(request.FILES['file'].name)[0]
            dataset.save()
            
            try:
                # Process uploaded file using Pandas
                process_dataset(dataset)
                
                # Deactivate all other datasets for this user and activate this one
                Dataset.objects.filter(user=request.user).exclude(pk=dataset.pk).update(is_active=False)
                dataset.is_active = True
                dataset.save()
                
                # Mark unsaved changes on UserProfile
                profile = request.user.userprofile
                profile.has_unsaved_changes = True
                profile.save()
                
                messages.success(request, f"Dataset '{dataset.name}' uploaded and processed successfully!")
                return redirect('dashboard:index')
            except Exception as e:
                # Clean up file and record if processing failed
                if dataset.file and os.path.exists(dataset.file.path):
                    try:
                        os.remove(dataset.file.path)
                    except Exception:
                        pass
                dataset.delete()
                messages.error(request, f"Failed to parse and process file: {str(e)}")
        else:
            messages.error(request, "Upload failed. Please check the file formatting.")
    else:
        form = DatasetUploadForm()
        
    return render(request, 'datasets/upload.html', {
        'form': form,
        'datasets': user_datasets,
        'active_dataset': active_dataset
    })

@login_required
def activate_dataset(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    
    # Deactivate others, activate this one
    Dataset.objects.filter(user=request.user).update(is_active=False)
    dataset.is_active = True
    dataset.save()
    
    profile = request.user.userprofile
    profile.has_unsaved_changes = True
    profile.save()
    
    messages.success(request, f"Active dataset switched to '{dataset.name}'.")
    return redirect('dashboard:index')

@login_required
def delete_dataset(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, user=request.user)
    name = dataset.name
    was_active = dataset.is_active
    
    # Delete actual file from storage
    if dataset.file and os.path.exists(dataset.file.path):
        try:
            os.remove(dataset.file.path)
        except Exception:
            pass
            
    dataset.delete()
    
    # If we deleted the active dataset, activate the next available one
    if was_active:
        next_dataset = Dataset.objects.filter(user=request.user).first()
        if next_dataset:
            next_dataset.is_active = True
            next_dataset.save()
            messages.info(request, f"Active dataset switched to '{next_dataset.name}'.")
            
    profile = request.user.userprofile
    profile.has_unsaved_changes = True
    profile.save()
    
    messages.success(request, f"Dataset '{name}' deleted successfully.")
    return redirect('datasets:upload')

def process_dataset(dataset):
    """
    Reads the dataset file using Pandas, extracts schema, rows/cols count,
    missing cells, duplicates, types, and generates preview data.
    """
    file_path = dataset.file.path
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel files.")
        
    row_count = int(df.shape[0])
    column_count = int(df.shape[1])
    missing_count = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())
    
    numeric_columns = []
    categorical_columns = []
    column_types = {}
    
    from pandas.api.types import is_numeric_dtype
    
    for col in df.columns:
        col_str = str(col)
        dtype = df[col].dtype
        column_types[col_str] = str(dtype)
        
        # Classify numeric vs categorical using pandas built-in type helpers
        if is_numeric_dtype(df[col]):
            numeric_columns.append(col_str)
        else:
            categorical_columns.append(col_str)
            
    # Create a JSON-safe preview (first 10 rows)
    # Replace NaN/NaT values with None so standard json encoder handles it
    df_preview = df.head(10).copy()
    
    # Convert non-numeric columns to string to ensure json serialization safety
    for col in df_preview.columns:
        if not is_numeric_dtype(df_preview[col]):
            df_preview[col] = df_preview[col].astype(str)
            
    # Replace NaN and Inf
    df_preview = df_preview.replace({np.nan: None, float('inf'): None, float('-inf'): None, 'nan': None, 'NaN': None, 'NaT': None, 'None': None})
    preview_data = df_preview.to_dict(orient='records')
    
    dataset.row_count = row_count
    dataset.column_count = column_count
    dataset.missing_values_count = missing_count
    dataset.duplicate_count = duplicate_count
    dataset.numeric_columns = numeric_columns
    dataset.categorical_columns = categorical_columns
    dataset.column_types = column_types
    dataset.preview_data = preview_data
    dataset.save()
