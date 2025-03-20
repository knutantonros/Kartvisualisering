"""
Main panel components for the Swedish regions visualization app.
"""
import pandas as pd
import streamlit as st
from visualization.mapplot import display_visualization
from config import APP_TITLE, APP_DESCRIPTION


def setup_page():
    """
    Set up the page configuration and display title and description.
    """
    # Title and description
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)


def show_visualization(lan_gdf, nuts2_gdf, trafikverket_gdf):
    """
    Display the visualization based on the processed data in session state.
    
    Args:
        lan_gdf (gpd.GeoDataFrame): GeoDataFrame with län boundaries
        nuts2_gdf (gpd.GeoDataFrame): GeoDataFrame with NUTS-2 boundaries
        trafikverket_gdf (gpd.GeoDataFrame): GeoDataFrame with Trafikverket region boundaries
    """
    # Create visualization based on processed data
    display_visualization(
        st.session_state['lan_data'],
        st.session_state['nuts2_data'],
        st.session_state.get('trafikverket_data', pd.DataFrame()),  # Add default value for backward compatibility
        lan_gdf,
        nuts2_gdf,
        trafikverket_gdf,
        st.session_state['map_type'],
        st.session_state['value_column'], 
        st.session_state['color_scheme'],
        st.session_state['width'],
        st.session_state['height']
    )


def show_welcome_info():
    """
    Display welcome information when no visualization is ready.
    """
    st.info("Välj dataalternativ och klicka på 'Generera visualisering' för att börja.")
    
    # Sample data format
    st.header("Om denna app")
    st.markdown("""
    Denna app låter dig visualisera data över svenska regioner, antingen efter:
    - **Län**: Sveriges 21 län
    - **NUTS-2 Regioner**: Europeiska statistiska regioner (8 regioner i Sverige)
    - **Trafikverket Regioner**: Trafikverkets 6 regioner (Syd, Norr, Mitt, Öst, Väst, Sydöst)
    
    Dina data bör innehålla:
    1. En kolumn med svenska länsnamn (t.ex. 'Stockholm', 'Uppsala') ELLER länskoder (t.ex. '01', '03')
    2. En kolumn med numeriska värden att visualisera
    
    Exempel-CSV:
    ```
    län,befolkning,bnp
    01,2396599,1500000
    03,395026,250000
    ...
    ```
    """)
