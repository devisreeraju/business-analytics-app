from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from datasets.models import Dataset
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
import datetime
import json
import os

# ─────────────────────────────────────────────────────────
#  PALETTE (matches CSS variables / Power BI feel)
# ─────────────────────────────────────────────────────────
COLORS = ['#1E3A8A', '#7C3AED', '#06B6D4', '#10B981', '#F59E0B',
          '#EF4444', '#3B82F6', '#A855F7', '#22D3EE', '#34D399']


# ─────────────────────────────────────────────────────────
#  COLUMN TYPE HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────
def _numeric_cols(df):
    from pandas.api.types import is_numeric_dtype
    return [c for c in df.columns if is_numeric_dtype(df[c])]


def _cat_cols(df):
    from pandas.api.types import is_numeric_dtype
    return [c for c in df.columns if not is_numeric_dtype(df[c])]


def _date_cols(df):
    from pandas.api.types import is_datetime64_any_dtype
    return [c for c in df.columns if is_datetime64_any_dtype(df[c])]


def _find_best_col(cols, target_keywords):
    """
    Finds the best matching column from target_keywords ordered list.
    First scans for exact matches (case-insensitive), then scans for containment.
    """
    # 1. Look for exact matches (case-insensitive)
    for kw in target_keywords:
        for c in cols:
            if c.lower().strip() == kw.lower().strip():
                return c
                
    # 2. Look for containment matches
    for kw in target_keywords:
        for c in cols:
            if kw.lower().strip() in c.lower():
                return c
                
    return None


def _clean_df_for_chart(df):
    """Clean the dataframe types to ensure safe json serialization."""
    from pandas.api.types import is_numeric_dtype
    df = df.copy()
    for col in df.columns:
        if is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = df[col].astype(str).replace({'nan': None, 'NaT': None, '<NA>': None})
    df = df.dropna(how='all')
    return df


# ─────────────────────────────────────────────────────────
#  KPI CALCULATOR
# ─────────────────────────────────────────────────────────
def compute_kpis(df):
    num = _numeric_cols(df)
    cat = _cat_cols(df)

    rev_col   = _find_best_col(df.columns, ['gross sales', 'gross_sales', 'sales', 'revenue', 'amount', 'total_amount', 'turnover', 'total'])
    prof_col  = _find_best_col(df.columns, ['profit', 'net profit', 'earnings', 'margin', 'net'])
    qty_col   = _find_best_col(df.columns, ['quantity', 'qty', 'units', 'volume', 'count'])
    ord_col   = _find_best_col(df.columns, ['order_id', 'order id', 'transaction_id', 'invoice'])
    cust_col  = _find_best_col(df.columns, ['customer', 'client', 'cust_id', 'user_id', 'buyer'])

    def _sum(col): return float(df[col].sum()) if col and col in df.columns else None
    def _nuniq(col): return int(df[col].nunique()) if col and col in df.columns else None

    revenue   = _sum(rev_col)   or (_sum(num[0]) if num else 0)
    profit    = _sum(prof_col)  or (revenue * 0.18)
    sales_qty = _sum(qty_col)   or (revenue / 15)
    orders    = _nuniq(ord_col) or int(df.shape[0])
    customers = _nuniq(cust_col) or (int(df[cat[0]].nunique()) if cat else orders // 3)
    aov       = (revenue / orders) if orders else 0

    return dict(revenue=revenue, profit=profit, sales=sales_qty,
                orders=orders, customers=customers, aov=aov)


# ─────────────────────────────────────────────────────────
#  FIGURE STYLING HELPER
# ─────────────────────────────────────────────────────────
def _style_figure(fig, theme, title):
    if not fig:
        return None
    text_color = '#0F172A' if theme == 'light' else '#F8FAFC'
    grid_color = '#E2E8F0' if theme == 'light' else '#243048'
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family='Inter, sans-serif',
        font_color=text_color,
        margin=dict(l=15, r=15, t=15, b=20),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=9)
        )
    )
    
    try:
        fig.update_xaxes(
            showgrid=True,
            gridcolor=grid_color,
            linecolor=grid_color,
            tickfont=dict(color=text_color, size=9)
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor=grid_color,
            linecolor=grid_color,
            tickfont=dict(color=text_color, size=9)
        )
    except Exception:
        pass
    return fig


# ─────────────────────────────────────────────────────────
#  AUTO CHART GENERATOR
# ─────────────────────────────────────────────────────────
def auto_generate_charts(df, theme='light'):
    charts = {}
    cols = list(df.columns)
    num_cols = _numeric_cols(df)
    cat_cols = _cat_cols(df)

    # 1. Gross Sales (Y-axis for sales metrics)
    gross_sales_col = _find_best_col(cols, ['gross sales', 'gross_sales', 'sales', 'revenue', 'amount', 'total_amount', 'turnover', 'total'])
    if not gross_sales_col:
        gross_sales_col = num_cols[0] if num_cols else None

    # 2. Profit
    profit_col = _find_best_col(cols, ['profit', 'net profit', 'earnings', 'margin', 'net', 'cost'])
    if not profit_col:
        other_nums = [c for c in num_cols if c != gross_sales_col]
        profit_col = other_nums[0] if other_nums else (gross_sales_col or None)

    # 3. Product
    product_col = _find_best_col(cols, ['product name', 'product_name', 'product', 'item', 'title'])
    if not product_col:
        product_col = cat_cols[0] if cat_cols else None

    # 4. Category
    category_col = _find_best_col(cols, ['category', 'dept', 'department', 'class', 'type'])
    if not category_col:
        other_cats = [c for c in cat_cols if c != product_col]
        category_col = other_cats[0] if other_cats else (product_col or None)

    # 5. Country
    country_col = _find_best_col(cols, ['country', 'state', 'city', 'location', 'nation'])
    if not country_col:
        other_cats = [c for c in cat_cols if c not in [product_col, category_col]]
        country_col = other_cats[0] if other_cats else (category_col or None)

    # 6. Region
    region_col = _find_best_col(cols, ['region', 'territory', 'zone', 'area'])
    if not region_col:
        other_cats = [c for c in cat_cols if c not in [product_col, category_col, country_col]]
        region_col = other_cats[0] if other_cats else (country_col or None)

    # 7. Month/Date
    month_col = _find_best_col(cols, ['month name', 'month_name', 'month', 'date', 'order_date', 'order date', 'year'])
    if not month_col:
        other_cats = [c for c in cat_cols if c not in [product_col, category_col, country_col, region_col]]
        month_col = other_cats[0] if other_cats else (region_col or None)

    # Helper: Chronological month sorting key
    def get_month_sort_key(month_str):
        m_order = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        val = str(month_str).lower().strip()
        if val.isdigit():
            return int(val)
        for k, order in m_order.items():
            if k in val:
                return order
        return 999

    # Diagnostic logging (Requirement 9)
    print("=== ANALYTICS DIAGNOSTICS ===")
    print(f"Dataframe Shape: {df.shape}")
    print(f"Dataframe Columns: {cols}")
    print("Selected columns for each visualization:")
    print(f"  - Gross Sales Column: {gross_sales_col}")
    print(f"  - Profit Column: {profit_col}")
    print(f"  - Product Column: {product_col}")
    print(f"  - Category Column: {category_col}")
    print(f"  - Country Column: {country_col}")
    print(f"  - Region Column: {region_col}")
    print(f"  - Month/Date Column: {month_col}")

    # ── CHART 1: Gross Sales by Product (Bar chart, Top 10) ─────────────────
    if product_col and gross_sales_col:
        d = df.groupby(product_col, as_index=False)[gross_sales_col].sum()
        d = d.sort_values(gross_sales_col, ascending=False).head(10)
        print(f"  - Chart 1 (bar_category) rows after aggregation: {d.shape[0]}")
        fig = px.bar(d, x=product_col, y=gross_sales_col, color_discrete_sequence=['#1E3A8A'])
        fig = _style_figure(fig, theme, f"Gross Sales by {product_col}")
        charts['bar_category'] = {
            'title': f"Gross Sales by {product_col}",
            'subtitle': "Top 10 performing products ranked by sales",
            'json': pio.to_json(fig)
        }

    # ── CHART 2: Gross Sales by Country (Pie chart) ────────────────────────
    if country_col and gross_sales_col:
        d = df.groupby(country_col, as_index=False)[gross_sales_col].sum()
        d = d.sort_values(gross_sales_col, ascending=False).head(15)
        print(f"  - Chart 2 (pie_region) rows after aggregation: {d.shape[0]}")
        fig = px.pie(d, names=country_col, values=gross_sales_col, color_discrete_sequence=COLORS)
        fig = _style_figure(fig, theme, f"Gross Sales by {country_col}")
        charts['pie_region'] = {
            'title': f"Gross Sales by {country_col}",
            'subtitle': "Geographic sales split",
            'json': pio.to_json(fig)
        }

    # ── CHART 3: Profit by Product (Horizontal Bar chart, descending) ───────
    if product_col and profit_col:
        d = df.groupby(product_col, as_index=False)[profit_col].sum()
        d = d.sort_values(profit_col, ascending=True).tail(15) # Ascending for H-Bar sorting
        print(f"  - Chart 3 (hbar_profit) rows after aggregation: {d.shape[0]}")
        fig = px.bar(d, x=profit_col, y=product_col, orientation='h', color_discrete_sequence=['#7C3AED'])
        fig = _style_figure(fig, theme, f"Profit by {product_col}")
        charts['hbar_profit'] = {
            'title': f"Profit by {product_col}",
            'subtitle': "Product profitability ranking",
            'json': pio.to_json(fig)
        }

    # ── CHART 4: Monthly Gross Sales Trend (Line chart, chronological) ──────
    if month_col and gross_sales_col:
        d = df.copy()
        d_grouped = d.groupby(month_col, as_index=False)[gross_sales_col].sum()
        d_grouped['_sort_key'] = d_grouped[month_col].apply(get_month_sort_key)
        d_grouped = d_grouped.sort_values('_sort_key')
        print(f"  - Chart 4 (line_trend) rows after aggregation: {d_grouped.shape[0]}")
        fig = px.line(d_grouped, x=month_col, y=gross_sales_col, color_discrete_sequence=['#06B6D4'])
        fig = _style_figure(fig, theme, "Monthly Gross Sales Trend")
        charts['line_trend'] = {
            'title': "Monthly Gross Sales Trend",
            'subtitle': "Chronological revenue performance",
            'json': pio.to_json(fig)
        }

    # ── CHART 5: Top 10 Month Names by Gross Sales (Bar chart) ──────────────
    if month_col and gross_sales_col:
        d = df.groupby(month_col, as_index=False)[gross_sales_col].sum()
        d = d.sort_values(gross_sales_col, ascending=False).head(10)
        print(f"  - Chart 5 (bar_top_cust) rows after aggregation: {d.shape[0]}")
        fig = px.bar(d, x=month_col, y=gross_sales_col, color_discrete_sequence=['#10B981'])
        fig = _style_figure(fig, theme, "Top Months by Gross Sales")
        charts['bar_top_cust'] = {
            'title': "Top Months by Gross Sales",
            'subtitle': "Highest performing months ranked descending",
            'json': pio.to_json(fig)
        }

    # ── CHART 6: Product Distribution (Donut chart) ─────────────────────────
    if product_col:
        d = df.groupby(product_col, as_index=False).size()
        d.columns = [product_col, 'Count']
        d = d.sort_values('Count', ascending=False).head(12)
        print(f"  - Chart 6 (donut_dist) rows after aggregation: {d.shape[0]}")
        fig = px.pie(d, names=product_col, values='Count', hole=0.4, color_discrete_sequence=COLORS)
        fig = _style_figure(fig, theme, "Product Distribution")
        charts['donut_dist'] = {
            'title': "Product Distribution",
            'subtitle': "Product transaction counts distribution",
            'json': pio.to_json(fig)
        }

    # ── CHART 7: Treemap (Category/Product hierarchy) ──────────────────────
    if category_col and product_col and gross_sales_col:
        path_list = [category_col]
        if product_col != category_col:
            path_list.append(product_col)
        d = df.groupby(path_list, as_index=False)[gross_sales_col].sum()
        d = d[d[gross_sales_col] > 0]
        print(f"  - Chart 7 (treemap) rows after aggregation: {d.shape[0]}")
        fig = px.treemap(d, path=path_list, values=gross_sales_col, color_discrete_sequence=COLORS)
        fig = _style_figure(fig, theme, f"Gross Sales Hierarchy")
        charts['treemap'] = {
            'title': "Sales Hierarchy Treemap",
            'subtitle': f"Treemap distribution of {gross_sales_col}",
            'json': pio.to_json(fig)
        }

    # ── CHART 8: Scatter Correlation (X=Gross Sales, Y=Profit) ──────────────
    if gross_sales_col and profit_col:
        df_sample = df.sample(min(4000, len(df)), random_state=42) if len(df) > 4000 else df
        color_col = category_col if category_col and category_col in df.columns else None
        print(f"  - Chart 8 (scatter) rows sampled: {df_sample.shape[0]}")
        fig = px.scatter(df_sample, x=gross_sales_col, y=profit_col, color=color_col, color_discrete_sequence=COLORS)
        fig = _style_figure(fig, theme, f"{gross_sales_col} vs {profit_col} Correlation")
        charts['scatter'] = {
            'title': "Sales vs Profit Correlation",
            'subtitle': f"Correlation plot of {gross_sales_col} vs {profit_col}",
            'json': pio.to_json(fig)
        }

    # ── CHART 9: Region Performance (Grouped Bar chart) ────────────────────
    if region_col and gross_sales_col and profit_col:
        d = df.groupby(region_col, as_index=False)[[gross_sales_col, profit_col]].sum()
        d = d.sort_values(gross_sales_col, ascending=False).head(12)
        print(f"  - Chart 9 (area_region) rows after aggregation: {d.shape[0]}")
        d_melt = d.melt(id_vars=[region_col], value_vars=[gross_sales_col, profit_col], var_name='Metric', value_name='Amount')
        fig = px.bar(d_melt, x=region_col, y='Amount', color='Metric', barmode='group', color_discrete_sequence=['#1E3A8A', '#7C3AED'])
        fig = _style_figure(fig, theme, f"Region Performance")
        charts['area_region'] = {
            'title': "Region Performance",
            'subtitle': "Gross Sales vs Profit comparison",
            'json': pio.to_json(fig)
        }
    print("=============================")

    return charts


# ─────────────────────────────────────────────────────────
#  MAIN VIEW
# ─────────────────────────────────────────────────────────
@login_required
def view(request):
    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()

    if not active_dataset:
        return render(request, 'analytics/view.html', {'active_dataset': None})

    file_path = active_dataset.file.path
    if not os.path.exists(file_path):
        messages.error(request, "Dataset file not found on disk.")
        return redirect('datasets:upload')

    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df = _clean_df_for_chart(df)
    except Exception as e:
        return render(request, 'analytics/view.html', {
            'active_dataset': active_dataset,
            'error_message': f"Could not load dataset: {e}"
        })

    try:
        theme = request.user.userprofile.theme_preference
    except Exception:
        theme = 'light'

    kpis   = compute_kpis(df)
    charts = auto_generate_charts(df, theme)

    stat = os.stat(file_path)
    upload_time    = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%b %d, %Y')
    refreshed_time = datetime.datetime.now().strftime('%H:%M:%S')

    return render(request, 'analytics/view.html', {
        'active_dataset':  active_dataset,
        'kpis':            kpis,
        'charts':          charts,
        'upload_time':     upload_time,
        'refreshed_time':  refreshed_time,
        'row_count':       active_dataset.row_count,
        'col_count':       active_dataset.column_count,
    })


# ─────────────────────────────────────────────────────────
#  AJAX REFRESH ALL CHARTS
# ─────────────────────────────────────────────────────────
@login_required
def update_chart_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST only'}, status=400)

    active_dataset = Dataset.objects.filter(user=request.user, is_active=True).first()
    if not active_dataset:
        return JsonResponse({'status': 'error', 'message': 'No active dataset'}, status=404)

    try:
        file_path = active_dataset.file.path
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df = _clean_df_for_chart(df)
        try:
            theme = request.user.userprofile.theme_preference
        except Exception:
            theme = 'light'
        charts = auto_generate_charts(df, theme)
        return JsonResponse({'status': 'success', 'charts': {k: v['json'] for k, v in charts.items()}})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
