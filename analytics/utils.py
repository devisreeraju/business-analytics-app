import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np

def generate_plotly_chart(df, chart_type, x_axis, y_axis=None, theme='light'):
    """
    Generates an interactive Plotly chart styled for Light/Dark themes and 
    returns its JSON representation for rendering client-side.
    Supports: bar, line, pie, donut, area, scatter, treemap, histogram, heatmap.
    """
    if df is None or df.empty:
        return None
        
    # Safeguard axis selection
    if not x_axis or x_axis not in df.columns:
        return None

    # Premium theme colors matching CSS
    colors = ['#1E3A8A', '#7C3AED', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
    
    # Determine text and line colors based on the active theme
    text_color = '#0F172A' if theme == 'light' else '#F8FAFC'
    grid_color = '#E2E8F0' if theme == 'light' else '#243048'
    
    # Handle missing y-axis for charts that require it
    from pandas.api.types import is_numeric_dtype
    if chart_type in ['bar', 'line', 'pie', 'donut', 'area', 'scatter', 'treemap', 'heatmap'] and not y_axis:
        numeric_cols = [c for c in df.columns if is_numeric_dtype(df[c])]
        if numeric_cols:
            y_axis = numeric_cols[0]
        else:
            # Fallback if no numeric column exists, just use count of rows
            df = df.groupby(x_axis).size().reset_index(name='Count')
            x_axis = x_axis
            y_axis = 'Count'

    fig = None
    try:
        if chart_type == 'bar':
            fig = px.bar(df, x=x_axis, y=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'line':
            fig = px.line(df, x=x_axis, y=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'pie':
            fig = px.pie(df, names=x_axis, values=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'donut':
            fig = px.pie(df, names=x_axis, values=y_axis, hole=0.4, color_discrete_sequence=colors)
        elif chart_type == 'area':
            fig = px.area(df, x=x_axis, y=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'treemap':
            # Treemap values must be positive. Filter values > 0 to prevent Plotly size errors.
            df_tree = df.copy()
            if y_axis and y_axis in df_tree.columns and is_numeric_dtype(df_tree[y_axis]):
                df_tree = df_tree[df_tree[y_axis] > 0]
            fig = px.treemap(df_tree, path=[x_axis], values=y_axis, color_discrete_sequence=colors)
        elif chart_type == 'histogram':
            fig = px.histogram(df, x=x_axis, color_discrete_sequence=colors)
        elif chart_type == 'heatmap':
            # Density heatmap using continuous color scales
            scale = 'Blues' if theme == 'light' else 'Viridis'
            fig = px.density_heatmap(df, x=x_axis, y=y_axis, color_continuous_scale=scale)
        else:
            fig = px.bar(df, x=x_axis, y=y_axis, color_discrete_sequence=colors)
    except Exception as e:
        print(f"Plotly generation error: {e}")
        return None

    # Custom layout styling
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family='Inter, sans-serif',
        font_color=text_color,
        margin=dict(l=15, r=15, t=15, b=20),
        showlegend=True if chart_type in ['pie', 'donut'] else False,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=9)
        )
    )
    
    # Format grid lines and ticks
    if chart_type not in ['pie', 'donut', 'treemap']:
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
    
    # Return JSON dump
    return pio.to_json(fig)
