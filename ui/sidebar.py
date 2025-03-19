"""
Sidebar components for the Swedish regions visualization app.
"""

import streamlit as st
import pandas as pd
from utils.data_utils import create_sample_data, identify_potential_region_columns, get_numeric_columns, process_data
from config import COLOR_SCHEMES, SIZE_PRESETS


def render_sidebar(lan_gdf, nuts2_gdf):
    """
    Render the sidebar components and handle data processing.
    
    Args:
        lan_gdf (gpd.GeoDataFrame): GeoDataFrame with län boundaries
        nuts2_gdf (gpd.GeoDataFrame): GeoDataFrame with NUTS-2 boundaries
        
    Returns:
        bool: Whether the visualization is ready to be displayed
    """
    with st.sidebar:
        st.header("Dataalternativ")
        
        # Option to use sample data or upload file
        data_option = st.radio("Välj datakälla:", ["Ladda upp en fil", "Använd exempeldata"])
        
        df = None
        if data_option == "Ladda upp en fil":
            uploaded_file = st.file_uploader("Ladda upp din CSV- eller Excel-fil", type=["csv", "xlsx"])
            
            if uploaded_file is not None:
                # Read the file
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.success("Filen laddades upp framgångsrikt!")
                    st.write("Förhandsgranskning av data:")
                    st.dataframe(df.head())
                except Exception as e:
                    st.error(f"Fel vid läsning av fil: {e}")
        else:
            # Use sample data
            sample_type = st.radio("Välj typ av exempeldata:", ["Län med kod", "Län med namn"])
            
            sample_codes_df, sample_names_df = create_sample_data()
            
            if sample_type == "Län med kod":
                df = sample_codes_df
                st.write("Förhandsgranskning av exempeldata:")
                st.dataframe(df.head())
            else:
                df = sample_names_df
                st.write("Förhandsgranskning av exempeldata:")
                st.dataframe(df.head())
        
        # Only show these options if we have data
        if df is not None:
            return render_visualization_options(df, lan_gdf, nuts2_gdf)
        
        return False


def render_visualization_options(df, lan_gdf, nuts2_gdf):
    """
    Render the visualization options in the sidebar and process data when requested.
    
    Args:
        df (pd.DataFrame): DataFrame with the data to visualize
        lan_gdf (gpd.GeoDataFrame): GeoDataFrame with län boundaries
        nuts2_gdf (gpd.GeoDataFrame): GeoDataFrame with NUTS-2 boundaries
        
    Returns:
        bool: Whether the visualization is ready to be displayed
    """
    st.header("Kartinställningar")
    
    # Determine possible region columns
    possible_region_cols = identify_potential_region_columns(df)
    default_region_col = possible_region_cols[0] if possible_region_cols else df.columns[0]
    
    region_column = st.selectbox(
        "Välj kolumnen med länsnamn eller länskoder:", 
        df.columns,
        index=df.columns.get_loc(default_region_col) if default_region_col in df.columns else 0
    )
    
    # Filter out the region column and non-numeric columns for value selection
    numeric_cols = get_numeric_columns(df)
    if numeric_cols:
        value_column = st.selectbox("Välj kolumnen med värden att visualisera:", numeric_cols)
    else:
        value_column = st.selectbox("Välj kolumnen med värden att visualisera:", 
                                 [col for col in df.columns if col != region_column])
    
    # Color scheme
    color_scheme = st.selectbox("Välj färgschema:", COLOR_SCHEMES)
    
    # Map type selection
    map_type = st.radio("Välj visualiseringsnivå:", ["Län", "NUTS-2 Regioner"])
    
    # Map size controls
    st.subheader("Diagramyta")
    
    # Size presets first (so they can override sliders)
    size_preset = st.radio(
        "Förinställd storlek:",
        list(SIZE_PRESETS.keys())
    )
    
    # Default values for the sliders based on preset
    if size_preset != "Anpassad":
        width, height = SIZE_PRESETS[size_preset]
    else:
        width_default, height_default = SIZE_PRESETS["Medium (8x6)"]
        # Show sliders only if "Anpassad" is selected
        width = st.slider("Bredd", min_value=4, max_value=16, value=width_default, step=1)
        height = st.slider("Höjd", min_value=3, max_value=12, value=height_default, step=1)
    
    # Process button
    if st.button("Generera visualisering"):
        with st.spinner("Bearbetar data och skapar visualisering..."):
            lan_data, nuts2_data = process_data(df, region_column, value_column)
            
            if not lan_data.empty or not nuts2_data.empty:
                # Store processed data and settings in session state
                st.session_state['lan_data'] = lan_data
                st.session_state['nuts2_data'] = nuts2_data
                st.session_state['map_type'] = map_type
                st.session_state['value_column'] = value_column
                st.session_state['color_scheme'] = color_scheme
                st.session_state['width'] = width
                st.session_state['height'] = height
                st.session_state['visualization_ready'] = True
                return True
            else:
                st.error("Kunde inte bearbeta data för visualisering.")
                return False
    
    return 'visualization_ready' in st.session_state and st.session_state['visualization_ready']
