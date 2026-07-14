import requests
import json
import re
import pandas as pd
import numpy as np

def generate_ai_report_from_mistral(dataset, api_key):
    """
    Constructs a rich prompt based on the active dataset's shape, schemas,
    statistics, and sample data. Sends it to Mistral AI chat API, then
    parses the resulting markdown response into database-savable sections.
    """
    if not api_key:
        raise ValueError("Mistral API Key is missing. Please configure it in your Settings.")
        
    # 1. Prepare dataset statistical summary to feed the AI
    file_path = dataset.file.path
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        raise IOError(f"Could not read dataset file: {str(e)}")
        
    # Calculate stats for numeric columns
    stats_summary = {}
    for col in dataset.numeric_columns:
        if col in df.columns:
            stats_summary[col] = {
                'mean': float(df[col].mean()),
                'max': float(df[col].max()),
                'min': float(df[col].min())
            }
            
    # Sample records (top 5 rows)
    df_sample = df.head(5).copy()
    
    from pandas.api.types import (
        is_numeric_dtype,
        is_string_dtype,
        is_object_dtype,
        is_datetime64_any_dtype,
        is_bool_dtype
    )
    
    # Process each column to prevent dtype serialization errors
    for col in df_sample.columns:
        if is_bool_dtype(df_sample[col]):
            df_sample[col] = df_sample[col].astype(bool)
        elif is_datetime64_any_dtype(df_sample[col]):
            df_sample[col] = df_sample[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif is_numeric_dtype(df_sample[col]):
            # Cast to standard float to avoid pandas nullable Int64 / pd.NA issues
            df_sample[col] = df_sample[col].astype(float)
        else:
            # Safely cast string, object, and mixed types
            df_sample[col] = df_sample[col].astype(str)
            
    # Clean up empty strings and other NaN variations for JSON safety
    df_sample = df_sample.replace({
        np.nan: None,
        float('inf'): None,
        float('-inf'): None,
        'nan': None,
        'NaN': None,
        'NaT': None,
        'None': None,
        '<NA>': None,
        '': None
    })
    
    # Generate clean, JSON-serializable records list
    sample_rows = []
    for record in df_sample.to_dict(orient='records'):
        clean_record = {}
        for k, v in record.items():
            if pd.isna(v) or v is pd.NA:
                clean_record[k] = None
            else:
                clean_record[k] = v
        sample_rows.append(clean_record)
    
    # 2. Build the detailed prompt
    prompt = f"""
You are an expert Enterprise Business Intelligence Analyst and Strategic Consultant. Your job is to analyze the following dataset properties and write a comprehensive, actionable business report.

Dataset Name: {dataset.name}
Total Records (Rows): {dataset.row_count}
Total Dimensions (Columns): {dataset.column_count}
Data Schema & Types: {json.dumps(dataset.column_types, indent=2)}

DATA QUALITY HEALTH:
- Missing Cell Count: {dataset.missing_values_count}
- Duplicate Rows Count: {dataset.duplicate_count}

NUMERICAL METRIC STATISTICS:
{json.dumps(stats_summary, indent=2)}

SAMPLE DATA RECORDS (Top 5 Rows):
{json.dumps(sample_rows, indent=2)}

INSTRUCTIONS:
Generate a thorough, data-driven report. You must adapt your advice specifically to the columns and data provided. If there are sales, dates, categories, names, or locations, use them to provide concrete insights. Do not use generic placeholders.

You MUST write the report using EXACTLY the following header names in Markdown (hashes included). Place your insights directly under each header:

# EXECUTIVE SUMMARY
(Provide a high-level summary of the dataset and key takeaways)

# BUSINESS HIGHLIGHTS
(Analyze the KPIs, sales performance, trend analysis, product performance, or regional results based on the columns)

# RISKS
(Discuss data health warnings, outliers, sales declines, cost concerns, inventory flags, or risk factors)

# OPPORTUNITIES
(Detail cost optimizations, revenue expansion opportunities, inventory recommendations, or regional expansions)

# RECOMMENDATIONS
(Provide concrete, actionable business decisions and strategic steps. Be specific to the dataset variables)

# FINAL CONCLUSION
(Give a brief final wrap-up and business conclusion)

Do not include any conversational preamble, intro, or styling notes. Return only the markdown with the headers above.
"""

    # 3. Call the Mistral API
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # We will use open-mistral-7b as it is fast, stable, and widely accessible.
    payload = {
        "model": "open-mistral-7b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        if response.status_code != 200:
            err_data = response.json()
            err_msg = err_data.get('message', 'Unknown error')
            raise Exception(f"Mistral API returned error (HTTP {response.status_code}): {err_msg}")
            
        result = response.json()
        raw_markdown = result['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        raise Exception("The connection to Mistral AI API timed out. Please try again.")
    except Exception as e:
        raise Exception(f"Failed to query Mistral AI: {str(e)}")

    # 4. Parse the Markdown into database sections
    sections = parse_raw_markdown_report(raw_markdown)
    return sections

def parse_raw_markdown_report(content):
    """
    Case-insensitive regex scanner to split the markdown report into structured fields.
    """
    sections = {
        'executive_summary': '',
        'business_highlights': '',
        'risks': '',
        'opportunities': '',
        'recommendations': '',
        'conclusion': ''
    }
    
    content_upper = content.upper()
    headers = [
        ('EXECUTIVE SUMMARY', 'executive_summary'),
        ('BUSINESS HIGHLIGHTS', 'business_highlights'),
        ('RISKS', 'risks'),
        ('OPPORTUNITIES', 'opportunities'),
        ('RECOMMENDATIONS', 'recommendations'),
        ('FINAL CONCLUSION', 'conclusion')
    ]
    
    indices = []
    for header_title, field_name in headers:
        # Search for "# HEADER_TITLE" or "## HEADER_TITLE"
        pattern = rf'(?:#+\s*){header_title}'
        matches = list(re.finditer(pattern, content_upper))
        if matches:
            indices.append((matches[0].start(), matches[0].end(), field_name))
            
    # Sort indices by their character positions in the text
    indices.sort()
    
    for i in range(len(indices)):
        start_idx, end_idx, field_name = indices[i]
        content_start = end_idx
        content_end = indices[i+1][0] if i+1 < len(indices) else len(content)
        
        section_text = content[content_start:content_end].strip()
        sections[field_name] = section_text
        
    # Fallback if no headers were matched
    if not any(sections.values()):
        sections['executive_summary'] = content
        sections['recommendations'] = "Detailed insights can be found in the Executive Summary."
        
    return sections
