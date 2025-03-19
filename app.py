"""
Main application file for the Swedish regions visualization app.
"""

import streamlit as st
import pandas as pd
from ui.sidebar import render_sidebar
from ui.main_panel import setup_page, show_welcome_info, show_visualization
from ui.custom_groups import render_custom_grouping_ui, display_custom_groups_analysis
from utils.geo_utils import load_geojson
from config import APP_TITLE, APP_ABOUT


def main():
    """
    Main function to run the application.
    """
    # Set page configuration - this must be the first Streamlit command
    st.set_page_config(
        page_title=APP_TITLE, 
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': APP_ABOUT
        }
    )
    
    # Set up the main page
    setup_page()
    
    # Load GeoJSON data as GeoDataFrames
    lan_gdf, nuts2_gdf = load_geojson()
    
    # Render sidebar and get visualization status
    visualization_ready = render_sidebar(lan_gdf, nuts2_gdf)
    
    # Main content area - display info message if no data, otherwise show visualization
    if not visualization_ready:
        show_welcome_info()
    else:
        # Check if we're in Län view or NUTS-2 view
        is_lan_view = st.session_state.get('map_type') == "Län"
        
        # If in Län view, show both tabs, otherwise just the standard visualization
        if is_lan_view:
            # Create tabs for different visualizations
            tab1, tab2 = st.tabs(["Standardvisualisering", "Egna regiongrupper"])
            
            with tab1:
                show_visualization(lan_gdf, nuts2_gdf)
            
            with tab2:
                # UI for creating custom region groups
                custom_groups = render_custom_grouping_ui()
                
                # If we have data and custom groups, show the analysis
                if 'lan_data' in st.session_state and st.session_state['lan_data'] is not None:
                    st.markdown("---")
                    display_custom_groups_analysis(
                        st.session_state['lan_data'],
                        'region_name',
                        st.session_state['value_column'],
                        lan_gdf
                    )
        else:
            # Just show the standard visualization for NUTS-2 view
            show_visualization(lan_gdf, nuts2_gdf)
            
            # Add an info message explaining why custom groups aren't available
            st.info("Egna regiongrupper är endast tillgängliga i Län-vyn. Byt till Län-vyn i sidopanelen för att använda denna funktion.")


if __name__ == "__main__":
    main()