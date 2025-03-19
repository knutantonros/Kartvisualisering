"""
Utility functions for handling custom region grouping in the Swedish regions visualization app.
"""

import streamlit as st
import pandas as pd
from config import LAN_MAPPING


def create_custom_region_group(df, region_name_column, value_column, custom_groups):
    """
    Create a DataFrame with custom region groupings based on user selection.
    
    Args:
        df (pd.DataFrame): Original DataFrame with region data
        region_name_column (str): Column name containing region names
        value_column (str): Column name containing values to aggregate
        custom_groups (dict): Dictionary mapping group names to lists of region names
        
    Returns:
        pd.DataFrame: DataFrame with custom region groups and aggregated values
    """
    # Create a new DataFrame to store the grouped data
    grouped_data = []
    
    # Process each custom group
    for group_name, regions in custom_groups.items():
        # Skip empty groups
        if not regions:
            continue
            
        # Filter the DataFrame for the regions in this group
        group_df = df[df[region_name_column].isin(regions)]
        
        # If we have data for this group, aggregate it
        if not group_df.empty:
            # Calculate the aggregated value (mean)
            aggregated_value = group_df[value_column].mean()
            
            # Add to the results
            grouped_data.append({
                'custom_group': group_name,
                value_column: aggregated_value,
                'regions': ', '.join(regions),
                'region_count': len(regions)
            })
    
    # Convert to DataFrame
    if grouped_data:
        return pd.DataFrame(grouped_data)
    else:
        return pd.DataFrame(columns=['custom_group', value_column, 'regions', 'region_count'])


def get_available_regions():
    """
    Get the list of available Swedish regions (län) for grouping.
    
    Returns:
        list: List of region names
    """
    return sorted(list(LAN_MAPPING.values()))


def get_unused_regions(custom_groups):
    """
    Get the list of regions that are not yet assigned to any custom group.
    
    Args:
        custom_groups (dict): Dictionary mapping group names to lists of region names
        
    Returns:
        list: List of region names that are not yet in any custom group
    """
    all_regions = set(get_available_regions())
    used_regions = set()
    
    # Collect all regions that are already in custom groups
    for group_name, regions in custom_groups.items():
        used_regions.update(regions)
    
    # Return the regions that are not yet used
    return sorted(list(all_regions - used_regions))