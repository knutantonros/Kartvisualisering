"""
Functions for creating maps and visualizations of Swedish regions with pattern fills.
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import pandas as pd
import geopandas as gpd
import numpy as np
import traceback
from utils.geo_utils import fig_to_base64
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon, Polygon, LineString


def create_matplotlib_map(data, gdf, location_col, value_column, color_scheme, width=8, height=6, 
                         is_nuts2=False, is_trafikverket=False):
    """
    Create a choropleth map of Sweden using matplotlib with NUTS-2, Län, and Trafikverket region support.
    
    Args:
        data (pd.DataFrame): DataFrame with the data to visualize
        gdf (gpd.GeoDataFrame): GeoDataFrame with the geographic boundaries
        location_col (str): Name of the column containing location names
        value_column (str): Name of the column containing values to visualize
        color_scheme (str): Matplotlib colormap name to use
        width (int): Width of the figure in inches
        height (int): Height of the figure in inches
        is_nuts2 (bool): Whether the visualization is for NUTS-2 regions
        is_trafikverket (bool): Whether the visualization is for Trafikverket regions
        
    Returns:
        matplotlib.figure.Figure: The created map figure
    """
    try:
        # Ensure the value column is numeric
        data[value_column] = pd.to_numeric(data[value_column], errors='coerce')
        
        # Create a figure with appropriate size
        fig, ax = plt.subplots(1, 1, figsize=(width, height))
        
        # Merge data with GeoDataFrame
        if is_nuts2:
            # For NUTS-2 regions, we need to handle the merge differently
            if 'NUTS_ID' in gdf.columns:
                # Extract NUTS code (e.g., 'SE11' from 'SE11 Stockholm')
                data['nuts_code'] = data[location_col].str.split(' ').str[0]
                
                # Merge on NUTS_ID
                merged_gdf = gdf.merge(data, left_on='NUTS_ID', right_on='nuts_code', how='inner')
            else:
                # Try to match based on name containing the region name
                matched_rows = []
                for _, data_row in data.iterrows():
                    region_name = data_row[location_col].split(' ', 1)[1] if ' ' in data_row[location_col] else data_row[location_col]
                    for _, gdf_row in gdf.iterrows():
                        if region_name.lower() in gdf_row['name'].lower():
                            matched_row = {**gdf_row.to_dict(), **data_row.to_dict()}
                            matched_rows.append(matched_row)
                            break
                
                if matched_rows:
                    merged_gdf = gpd.GeoDataFrame(matched_rows, geometry='geometry')
                else:
                    st.error(f"No matches found between NUTS-2 regions in data and GeoJSON.")
                    return None
        elif is_trafikverket:
            # For Trafikverket regions, merge on the region name
            merged_gdf = gdf.merge(data, left_on='name', right_on=location_col, how='inner')
        else:
            # For län, merge as before
            merged_gdf = gdf.merge(data, left_on='name', right_on=location_col, how='inner')
        
        # Check if the merge was successful
        if merged_gdf.empty:
            st.error("Merge resulted in empty dataframe. Check column values for matching.")
            return None
        
        # Remove rows with NaN values
        merged_gdf = merged_gdf.dropna(subset=[value_column])
        
        # Normalize the data for coloring
        vmin = merged_gdf[value_column].min()
        vmax = merged_gdf[value_column].max()
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        
        # Get the colormap
        try:
            cmap = plt.get_cmap(color_scheme)
        except ValueError:
            st.warning(f"Color scheme '{color_scheme}' not found, using 'viridis' instead.")
            cmap = plt.get_cmap('viridis')
        
        # Add the map title based on visualization type
        #title = "Län i Sverige"
        #if is_nuts2:
            #title = "NUTS-2 Regioner i Sverige"
        #elif is_trafikverket:
            #title = "Trafikverket Regioner i Sverige"
        
        #plt.title(title, fontsize=14, pad=20)
        
        # For Trafikverket regions, treat all regions the same
        if is_trafikverket:
            # Plot all regions without borders
            merged_gdf.plot(
                column=value_column, 
                cmap=cmap, 
                linewidth=0,  # No borders
                ax=ax, 
                edgecolor='none',  # No borders
                norm=norm
            )
            
            # Add text labels in the center of each region
            for idx, row in merged_gdf.iterrows():
                centroid = row['geometry'].centroid
                text = ax.text(
                    centroid.x, centroid.y, 
                    row['name'], 
                    ha='center', va='center',
                    fontsize=12, fontweight='bold',
                    bbox=dict(facecolor='white', alpha=1, boxstyle='round,pad=0.3')
                )
        else:
            # For län and NUTS-2, plot with borders
            merged_gdf.plot(
                column=value_column, 
                cmap=cmap, 
                linewidth=1,
                ax=ax, 
                edgecolor='white',
                norm=norm
            )
        
        # Clean up the plot
        ax.set_axis_off()
        
        # Add a colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label(value_column)
        
        # Tight layout to remove excess whitespace
        plt.tight_layout()
        
        return fig
    
    except Exception as e:
        # More detailed error handling
        st.error(f"Error creating matplotlib map: {e}")
        traceback.print_exc()
        return None


def create_custom_groups_map(data, gdf, custom_groups, value_column, color_scheme, width=8, height=6, show_borders=False, show_labels=False):
    """
    Create a map showing custom region groups without pattern fills.
    
    Args:
        data (pd.DataFrame): DataFrame with the data to visualize
        gdf (gpd.GeoDataFrame): GeoDataFrame with the geographic boundaries
        custom_groups (dict): Dictionary of custom groups
        value_column (str): Name of the column containing values to visualize
        color_scheme (str): Matplotlib colormap name to use
        width (int): Width of the figure in inches
        height (int): Height of the figure in inches
        show_borders (bool): Whether to show borders between groups (default False)
        show_labels (bool): Whether to show labels in the map
        
    Returns:
        matplotlib.figure.Figure: The created map figure
    """
    try:
        # Create a figure with appropriate size
        fig, ax = plt.subplots(1, 1, figsize=(width, height), facecolor='white')
        
        # Get the colormap
        try:
            cmap = plt.get_cmap(color_scheme)
        except ValueError:
            st.warning(f"Color scheme '{color_scheme}' not found, using 'viridis' instead.")
            cmap = plt.get_cmap('viridis')
        
        # First, calculate the average value for each group
        group_values = {}
        for group_name, regions in custom_groups.items():
            if not regions:
                continue
                
            # Get the mean value for this group
            try:
                group_value = data[data['region_name'].isin(regions)][value_column].mean()
                group_values[group_name] = group_value
            except:
                group_values[group_name] = float('nan')
        
        # Create a base map to set the extent
        gdf.plot(ax=ax, color='none', edgecolor='none')
        
        # Normalize the data for coloring
        values = [v for v in group_values.values() if not np.isnan(v)]
        if values:
            vmin, vmax = min(values), max(values)
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        else:
            norm = mcolors.Normalize(vmin=0, vmax=1)
        
        # Create legend patches
        legend_handles = []
        
        # Plot each group of regions with solid fills (no patterns) and collect legend handles
        for i, (group_name, regions) in enumerate(custom_groups.items()):
            if not regions:
                continue
            
            # Get value and color for this group
            value = group_values.get(group_name)
            if pd.isna(value):
                color = 'gray'
            else:
                color = cmap(norm(value))
            
            # Create a patch for the legend (no hatching)
            legend_patch = mpatches.Patch(
                facecolor=color, 
                edgecolor='black' if show_borders else 'none',
                label=group_name
            )
            legend_handles.append(legend_patch)
            
            # Get regions for this group
            group_regions = gdf[gdf['name'].isin(regions)]
            
            # Plot with GeoPandas (no hatching, no borders)
            group_regions.plot(
                ax=ax,
                color=color,
                edgecolor='none',  # Always set to 'none' to remove borders
                linewidth=0,
                alpha=0.9
            )
        
        # Add labels if requested
        if show_labels:
            for group_name, regions in custom_groups.items():
                if not regions:
                    continue
                    
                # Filter regions for this group
                group_regions = gdf[gdf['name'].isin(regions)]
                
                if not group_regions.empty:
                    # Find centroid of the entire group
                    all_geoms = unary_union(group_regions.geometry)
                    centroid = all_geoms.centroid
                    
                    # Add text label with white outline for better visibility
                    text = ax.text(
                        centroid.x, centroid.y, 
                        group_name, 
                        fontsize=10, 
                        fontweight='bold',
                        ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3')
                    )
                    # Add white outline to text for better visibility
                    text.set_path_effects([
                        path_effects.Stroke(linewidth=2, foreground='white'),
                        path_effects.Normal()
                    ])
        
        # Clean up the plot
        ax.set_axis_off()
        
        # Add a colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
        cbar.set_label(value_column)
        
        # Add a legend with the colors (no patterns)
        if legend_handles:
            ax.legend(
                handles=legend_handles,
                loc='lower right', 
                framealpha=0.7, 
                frameon=True,
                title=""
            )
        
        # Tight layout to remove excess whitespace
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        # More detailed error handling
        st.error(f"Error creating custom groups map: {e}")
        traceback.print_exc()
        return None


def display_visualization(lan_data, nuts2_data, trafikverket_data, lan_gdf, nuts2_gdf, trafikverket_gdf, 
                         map_type, value_column, color_scheme, width=8, height=6):
    """
    Create and display the visualization with data summary and download options.
    
    Args:
        lan_data (pd.DataFrame): DataFrame with län-level data
        nuts2_data (pd.DataFrame): DataFrame with NUTS-2 level data
        trafikverket_data (pd.DataFrame): DataFrame with Trafikverket region data
        lan_gdf (gpd.GeoDataFrame): GeoDataFrame with län boundaries
        nuts2_gdf (gpd.GeoDataFrame): GeoDataFrame with NUTS-2 boundaries
        trafikverket_gdf (gpd.GeoDataFrame): GeoDataFrame with Trafikverket boundaries
        map_type (str): Type of map to display ("Län", "NUTS-2 Regioner", or "Trafikverket Regioner")
        value_column (str): Name of the column containing values to visualize
        color_scheme (str): Matplotlib colormap name to use
        width (int): Width of the figure in inches
        height (int): Height of the figure in inches
    """
    try:
        st.header("Visualisering")
        
        # Determine which data to use
        is_nuts2 = False
        is_trafikverket = False
        
        if map_type == "Län" and not lan_data.empty:
            gdf = lan_gdf
            data = lan_data
            location_col = 'region_name'
        elif map_type == "NUTS-2 Regioner" and not nuts2_data.empty:
            gdf = nuts2_gdf
            data = nuts2_data
            location_col = 'nuts2_region'
            is_nuts2 = True
        elif map_type == "Trafikverket Regioner" and not trafikverket_data.empty:
            gdf = trafikverket_gdf
            data = trafikverket_data
            location_col = 'trafikverket_region'
            is_trafikverket = True
        else:
            st.error("Inga data tillgängliga för visualisering.")
            return
        
        # Use a container with max width to control the map size
        with st.container():
            # Create the matplotlib visualization
            fig = create_matplotlib_map(data, gdf, location_col, value_column, color_scheme, width, height, 
                                        is_nuts2=is_nuts2, is_trafikverket=is_trafikverket)
            
            if fig:
                # Display the map in Streamlit with a set width
                col1, col2, col3 = st.columns([1, 3, 1])  # Use columns to center and constrain the map
                with col2:
                    st.pyplot(fig, use_container_width=True)  # This helps constrain the image
                
                # Create download button
                img_base64, img_bytes = fig_to_base64(fig)
                
                # Create a container with a header for the download
                st.subheader("Ladda ner visualisering")
                st.markdown("Klicka nedan för att ladda ner en PNG-bild som endast visar Sverige med förklaringen:")
                href = f'<a href="data:image/png;base64,{img_base64}" download="sverige_{map_type.lower().replace(" ", "_")}.png" class="download-btn" style="display: inline-block; padding: 0.5rem 1rem; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 0.5rem 0;">⬇️ Ladda ner Sverigekarta som PNG</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                # Data summary
                st.header("Datasammanfattning")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Högsta värde", 
                            f"{data[value_column].max():.2f}")
                    st.markdown(f"Region: <span style='color:green'>{data.loc[data[value_column].idxmax(), location_col]}</span>", unsafe_allow_html=True)
                with col2:
                    st.metric("Lägsta värde", 
                            f"{data[value_column].min():.2f}")
                    st.markdown(f"Region: <span style='color:red'>{data.loc[data[value_column].idxmin(), location_col]}</span>", unsafe_allow_html=True)
                with col3:
                    st.metric("Genomsnitt", f"{data[value_column].mean():.2f}")
                
                # Add download button for processed data
                st.header("Ladda ner bearbetade data")
                csv = data.to_csv(index=False)
                st.download_button(
                    label=f"Ladda ner {map_type}-data som CSV",
                    data=csv,
                    file_name=f"{'lan' if map_type == 'Län' else 'nuts2' if map_type == 'NUTS-2 Regioner' else 'trafikverket'}_bearbetade_data.csv",
                    mime="text/csv",
                )
    except Exception as e:
        st.error(f"Fel vid skapande av visualisering: {e}")
        traceback.print_exc()
