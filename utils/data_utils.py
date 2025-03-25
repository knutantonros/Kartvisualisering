"""
Utility functions for data processing in the Swedish regions visualization app.
"""

import pandas as pd
import streamlit as st
from config import LAN_MAPPING, NUTS2_MAPPING

def create_sample_data():
    """
    Create sample datasets for demonstration purposes.
    
    Returns:
        tuple: Two DataFrames - one with län codes and another with län names
    """
    lan_codes = list(LAN_MAPPING.keys())
    lan_names = list(LAN_MAPPING.values())
    
    # Create sample with län codes
    sample_codes_df = pd.DataFrame({
        'lan_kod': lan_codes,
        'befolkning': [2396599, 395026, 299401, 468387, 365010, 201469, 245446, 
                      61001, 158453, 1402425, 339367, 1744859, 282414, 304805, 
                      278967, 287966, 287502, 244193, 132054, 274154, 249693],
        'bnp_per_capita': [650000, 400000, 380000, 390000, 420000, 370000, 360000,
                          380000, 350000, 420000, 390000, 450000, 350000, 380000,
                          390000, 360000, 350000, 370000, 380000, 400000, 410000]
    })
    
    # Create sample with län names
    sample_names_df = pd.DataFrame({
        'lan_namn': lan_names,
        'arbetslöshet': [6.2, 7.1, 8.3, 7.9, 6.5, 8.2, 7.8, 6.9, 8.5, 
                         9.2, 6.7, 7.0, 7.6, 7.4, 8.1, 7.3, 9.0, 8.4, 
                         7.2, 6.8, 7.7]
    })
    
    return sample_codes_df, sample_names_df


def process_data(df, region_column, value_column):
    """
    Process the uploaded or sample data to prepare it for visualization.
    
    Args:
        df (pd.DataFrame): Input dataframe with region and value data
        region_column (str): Name of the column containing region identifiers
        value_column (str): Name of the column containing values to visualize
        
    Returns:
        tuple: Three processed DataFrames - one for län, one for NUTS-2, and one for Trafikverket regions
    """
    try:
        # Ensure the data is properly formatted
        processed_df = df.copy()
        
        # Convert region column to string
        processed_df[region_column] = processed_df[region_column].astype(str)
        
        # Handle län codes with leading zeros that might have been dropped
        # Add leading zero if it's a one-digit number
        processed_df[region_column] = processed_df[region_column].apply(
            lambda x: '0' + x if x.isdigit() and len(x) == 1 else x
        )
        
        # Mapping strategy
        def map_to_region(input_region):
            # First try direct mapping of codes to läns
            if input_region in LAN_MAPPING:
                return LAN_MAPPING[input_region]
            
            # If not a code, check if it's already a län name
            if input_region in LAN_MAPPING.values():
                return input_region
            
            # If not a code or län name, try to match case-insensitively
            for code, name in LAN_MAPPING.items():
                if input_region.lower() == name.lower():
                    return name
            
            # If no match found, return the original input
            return input_region
        
        # Map to region names
        processed_df['region_name'] = processed_df[region_column].apply(map_to_region)
        
        # Add NUTS-2 region
        processed_df['nuts2_region'] = processed_df['region_name'].map(NUTS2_MAPPING)
        
        # Handle numeric data - ensure value_column is numeric
        try:
            processed_df[value_column] = pd.to_numeric(processed_df[value_column], errors='coerce')
            if processed_df[value_column].isna().any():
                st.warning(f"Some values in column '{value_column}' could not be converted to numbers and were set to NaN.")
        except Exception as e:
            st.error(f"Error converting '{value_column}' to numeric value: {e}")
        
        # Drop rows with NaN in necessary columns
        processed_df = processed_df.dropna(subset=['region_name', value_column])
        
        # For NUTS-2, also drop rows with NaN in nuts2_region
        nuts2_data = processed_df.dropna(subset=['nuts2_region'])
        
        # Process for Trafikverket regions
        from utils.trafikverket_regions import process_trafikverket_data
        trafikverket_data = process_trafikverket_data(processed_df, region_column, value_column)
        
        # Aggregate by län and NUTS-2 if needed
        lan_data = processed_df.groupby('region_name')[value_column].mean().reset_index()
        nuts2_data = nuts2_data.groupby('nuts2_region')[value_column].mean().reset_index()
        
        # Handle empty dataframes
        if len(lan_data) == 0 and len(nuts2_data) == 0 and len(trafikverket_data) == 0:
            st.error("No valid data to visualize after processing. Check your input data.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        return lan_data, nuts2_data, trafikverket_data
    except Exception as e:
        st.error(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


def identify_potential_region_columns(df):
    """
    Identify columns that might contain region data based on naming conventions.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        list: List of column names that might contain region data
    """
    possible_region_cols = [col for col in df.columns if any(
        x in col.lower() for x in ['lan', 'län', 'region', 'county', 'code', 'kod', 'namn']
    )]
    
    return possible_region_cols or [df.columns[0]]


def get_numeric_columns(df):
    """
    Get numeric columns from a dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        list: List of numeric column names
    """
    return df.select_dtypes(include=['number']).columns.tolist()
