"""
Utility functions for handling geographic data in the Swedish regions visualization app.
"""
import pandas as pd
import streamlit as st
import geopandas as gpd
import requests
import traceback
from config import LAN_GEOJSON_URL, NUTS2_GEOJSON_URL, NUTS_ID_TO_NAME


# Separate function for loading GeoJSON files, which can be cached
@st.cache_data
def _load_base_geojson():
    """
    Load the base GeoJSON files for Swedish län and NUTS-2 regions.
    
    Returns:
        tuple: Two GeoDataFrames - one for län and one for NUTS-2 regions
    """
    try:
        # Load Swedish län GeoJSON
        lan_response = requests.get(LAN_GEOJSON_URL)
        lan_geojson = lan_response.json()
        lan_gdf = gpd.GeoDataFrame.from_features(lan_geojson["features"])
        
        # Download Eurostat NUTS-2 GeoJSON for Sweden
        nuts2_response = requests.get(NUTS2_GEOJSON_URL)
        nuts2_geojson = nuts2_response.json()
        
        # Filter for Swedish NUTS-2 regions
        swedish_nuts2_features = [
            feature for feature in nuts2_geojson["features"] 
            if feature["properties"]["NUTS_ID"].startswith("SE")
        ]
        
        # Convert to GeoDataFrame
        nuts2_gdf = gpd.GeoDataFrame.from_features(swedish_nuts2_features)
        
        # Check and set the name column correctly
        if 'NUTS_NAME' in nuts2_gdf.columns:
            nuts2_gdf['name'] = nuts2_gdf['NUTS_NAME']
        elif 'NAME' in nuts2_gdf.columns:
            nuts2_gdf['name'] = nuts2_gdf['NAME']
        else:
            # If neither column exists, create a mapping from NUTS_ID to our format
            if 'NUTS_ID' in nuts2_gdf.columns:
                nuts2_gdf['name'] = nuts2_gdf['NUTS_ID'].map(NUTS_ID_TO_NAME)
            else:
                st.warning("Could not find appropriate columns in NUTS-2 GeoJSON. Visualization may not work correctly.")
        
        return lan_gdf, nuts2_gdf
    
    except Exception as e:
        st.error(f"Error loading GeoJSON data: {e}")
        traceback.print_exc()
        return None, None


def load_geojson():
    """
    Load GeoJSON files and create Trafikverket regions.
    
    Returns:
        tuple: Three GeoDataFrames - one for län, one for NUTS-2 regions, and one for Trafikverket regions
    """
    try:
        # Load the base GeoJSON files using the cached function
        lan_gdf, nuts2_gdf = _load_base_geojson()
        
        if lan_gdf is not None and nuts2_gdf is not None:
            # Create Trafikverket regions from län GeoDataFrame
            from utils.trafikverket_regions import create_trafikverket_regions
            trafikverket_gdf = create_trafikverket_regions(_input_gdf=lan_gdf)
            
            return lan_gdf, nuts2_gdf, trafikverket_gdf
        else:
            return None, None, None
    
    except Exception as e:
        st.error(f"Error preparing GeoJSON data: {e}")
        traceback.print_exc()
        return None, None, None


def fig_to_base64(fig):
    """
    Convert a matplotlib figure to base64 string for embedding.
    
    Args:
        fig (matplotlib.figure.Figure): Matplotlib figure to convert
        
    Returns:
        tuple: Base64 encoded string and raw bytes of the image
    """
    from io import BytesIO
    import base64
    
    buf = BytesIO()
    # Use white background instead of light gray
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', transparent=False, pad_inches=0)
    buf.seek(0)
    img_bytes = buf.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode()
    buf.close()
    return img_base64, img_bytes
