"""
Utility functions for handling Trafikverket regions in the Swedish regions visualization app.
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon, Polygon
import traceback

# Define Trafikverket region mapping
TRAFIKVERKET_REGIONS = {
    # Syd (South)
    'Skåne': 'Syd',
    'Kronoberg': 'Syd',
    'Blekinge': 'Syd',
    
    # Norr (North)
    'Västernorrland': 'Norr',
    'Jämtland': 'Norr',
    'Västerbotten': 'Norr',
    'Norrbotten': 'Norr',
    
    # Mitt (Middle)
    'Uppsala': 'Mitt',
    'Södermanland': 'Mitt',
    'Västmanland': 'Mitt',
    'Värmland': 'Mitt',
    'Örebro': 'Mitt',
    'Dalarna': 'Mitt',
    'Gävleborg': 'Mitt',
    
    # Öst (East)
    'Stockholm': 'Öst',
    'Gotland': 'Öst',
    
    # Väst (West)
    'Halland': 'Väst',
    'Västra Götaland': 'Väst',
    
    # Sydöst (Southeast)
    'Jönköping': 'Sydöst',
    'Kalmar': 'Sydöst',
    'Östergötland': 'Sydöst'
}

# Trafikverket region IDs (matching the notebook)
TRAFIKVERKET_IDS = {
    'Syd': '26',
    'Norr': '27',
    'Mitt': '28',
    'Öst': '29',
    'Väst': '30',
    'Sydöst': '31'
}


def create_trafikverket_regions(_input_gdf):
    """
    Create a GeoDataFrame with Trafikverket regions by merging län boundaries.
    
    Args:
        _input_gdf (gpd.GeoDataFrame): GeoDataFrame with län boundaries
        
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with Trafikverket region boundaries
    """
    try:
        # Make a copy of the original GeoDataFrame to avoid modifying it
        working_gdf = _input_gdf.copy()
        
        # Normalize county names (remove ' län' suffix if present)
        working_gdf['county_name'] = working_gdf['name'].apply(
            lambda x: x.replace(' län', '') if isinstance(x, str) and ' län' in x else x
        )
        
        # Create a dictionary to store region geometries
        region_geometries = {}
        
        # Process each Trafikverket region
        for region_name in set(TRAFIKVERKET_REGIONS.values()):
            # Get counties in this region
            counties = [county for county, region in TRAFIKVERKET_REGIONS.items() 
                       if region == region_name]
            
            # Get geometries for these counties
            county_geometries = []
            for county in counties:
                matching_geoms = working_gdf[working_gdf['county_name'] == county]['geometry']
                if not matching_geoms.empty:
                    county_geometries.extend(matching_geoms.tolist())
            
            # If we found geometries, merge them
            if county_geometries:
                merged_geometry = unary_union(county_geometries)
                region_geometries[region_name] = merged_geometry
        
        # Create a new GeoDataFrame with the merged regions
        regions_data = []
        for region_name, geometry in region_geometries.items():
            regions_data.append({
                'name': region_name,
                'id': TRAFIKVERKET_IDS.get(region_name, ''),
                'geometry': geometry
            })
        
        # Create the GeoDataFrame
        if regions_data:
            trafikverket_gdf = gpd.GeoDataFrame(regions_data, geometry='geometry')
            if hasattr(_input_gdf, 'crs'):
                trafikverket_gdf.crs = _input_gdf.crs
            return trafikverket_gdf
        else:
            st.warning("Kunde inte skapa Trafikverket-regioner. Kontrollera att länsdata finns tillgänglig.")
            return gpd.GeoDataFrame()
            
    except Exception as e:
        st.error(f"Fel vid skapande av Trafikverket-regioner: {e}")
        traceback.print_exc()
        return gpd.GeoDataFrame()


def map_to_trafikverket_region(county_name):
    """
    Map a county name to its corresponding Trafikverket region.
    
    Args:
        county_name (str): The name of the county
        
    Returns:
        str: The name of the Trafikverket region
    """
    # Remove ' län' suffix if present
    if isinstance(county_name, str):
        clean_name = county_name.replace(' län', '') if ' län' in county_name else county_name
        return TRAFIKVERKET_REGIONS.get(clean_name, '')
    return ''


def process_trafikverket_data(df, region_column, value_column):
    """
    Process data for Trafikverket region visualization.
    
    Args:
        df (pd.DataFrame): DataFrame with the region data
        region_column (str): Column name containing region names or codes
        value_column (str): Column name containing values to visualize
        
    Returns:
        pd.DataFrame: Processed DataFrame with data aggregated by Trafikverket region
    """
    try:
        # Copy the input DataFrame to avoid modifying the original
        processed_df = df.copy()
        
        # Map the region column to Trafikverket regions
        processed_df['trafikverket_region'] = processed_df['region_name'].apply(map_to_trafikverket_region)
        
        # Remove rows without a valid Trafikverket region
        processed_df = processed_df[processed_df['trafikverket_region'] != '']
        
        # If we have no data after filtering, return an empty DataFrame
        if processed_df.empty:
            return pd.DataFrame()
        
        # Group by Trafikverket region and calculate the mean value
        trafikverket_data = processed_df.groupby('trafikverket_region')[value_column].mean().reset_index()
        
        return trafikverket_data
        
    except Exception as e:
        st.error(f"Fel vid bearbetning av data för Trafikverket-regioner: {e}")
        traceback.print_exc()
        return pd.DataFrame()
