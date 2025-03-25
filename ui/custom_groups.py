"""
UI components for creating and managing custom region groups.
"""

import streamlit as st
import pandas as pd
import random
from utils.region_groups import get_available_regions, create_custom_region_group, get_unused_regions
from visualization.mapplot import create_custom_groups_map


def render_custom_grouping_ui():
    """
    Render UI for creating and managing custom region groups.
    
    Returns:
        dict: Dictionary mapping group names to lists of regions
    """
    st.header("Egna regiongrupper")
    st.markdown("Här kan du skapa egna grupper av regioner för analys.")
    
    # Initialize session state for groups if not exists
    if 'custom_groups' not in st.session_state:
        st.session_state.custom_groups = {}
        
    # Initialize empty key for form submissions
    form_key = st.session_state.get('form_key', 0)
    
    # Get unused regions - län that aren't already in a group
    available_regions = get_unused_regions(st.session_state.custom_groups)
    
    # Add button to create 4 random groups
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Skapa 4 slumpmässiga grupper"):
            create_random_groups()
            st.rerun()
    
    # UI for creating a new group
    with st.expander("Skapa ny regiongrupp", expanded=not st.session_state.custom_groups):
        # Use a form with unique key for proper clearing
        with st.form(key=f"new_group_form_{form_key}"):
            new_group_name = st.text_input("Namn på gruppen")
            
            # Multi-select dropdown for regions - only showing unused regions
            selected_regions = st.multiselect(
                "Välj regioner att inkludera:",
                options=available_regions,
                default=[]
            )
            
            # Show message if all regions are used
            if not available_regions:
                st.info("Alla regioner har redan tilldelats till grupper. Ta bort en grupp för att frigöra regioner.")
            
            # Form submission button
            submit_button = st.form_submit_button(label="Lägg till grupp")
            
        if submit_button:
            if new_group_name and selected_regions:
                # Add the new group to our session state
                st.session_state.custom_groups[new_group_name] = selected_regions
                
                # Increment form key to force form reset
                st.session_state.form_key = form_key + 1
                
                st.success(f"Gruppen '{new_group_name}' har skapats med {len(selected_regions)} regioner.")
                st.rerun()
            else:
                st.error("Du måste ange ett namn och välja minst en region.")
    
    # Show existing groups and allow editing
    if st.session_state.custom_groups:
        st.subheader("Mina regiongrupper")
        
        for group_name, regions in list(st.session_state.custom_groups.items()):
            with st.expander(f"{group_name} ({len(regions)} regioner)"):
                # Display current regions in the group
                st.write("Nuvarande regioner:")
                st.write(", ".join(regions))
                
                # UI to edit the group
                col1, col2 = st.columns(2)
                
                # Edit regions in the group
                with col1:
                    # Get regions not used in OTHER groups (the current regions plus any unused)
                    other_groups_regions = set()
                    for other_name, other_regions in st.session_state.custom_groups.items():
                        if other_name != group_name:
                            other_groups_regions.update(other_regions)
                    
                    # Available regions for this group: all regions minus those in other groups
                    all_regions = set(get_available_regions())
                    available_for_group = sorted(list(all_regions - other_groups_regions))
                    
                    edit_regions = st.multiselect(
                        "Redigera regioner:",
                        options=available_for_group,
                        default=regions,
                        key=f"edit_{group_name}"
                    )
                    
                    if st.button("Uppdatera regioner", key=f"update_{group_name}"):
                        st.session_state.custom_groups[group_name] = edit_regions
                        st.success(f"Gruppen '{group_name}' har uppdaterats.")
                        st.rerun()
                
                # Delete group button
                with col2:
                    if st.button("Ta bort grupp", key=f"delete_{group_name}"):
                        del st.session_state.custom_groups[group_name]
                        st.warning(f"Gruppen '{group_name}' har tagits bort.")
                        st.rerun()
    
    return st.session_state.custom_groups


def create_random_groups():
    """
    Create 4 random groups of regions.
    """
    # Clear any existing groups
    st.session_state.custom_groups = {}
    
    # Get all available regions
    all_regions = get_available_regions()
    
    # Shuffle regions to randomize
    random_regions = list(all_regions)
    random.shuffle(random_regions)
    
    # Calculate regions per group (approximate)
    total_regions = len(random_regions)
    regions_per_group = total_regions // 4
    
    # Create 4 groups with different sizes
    group_names = ["Norra", "Södra", "Östra", "Västra"]
    
    start_idx = 0
    for i, name in enumerate(group_names):
        # Last group gets all remaining regions
        if i == 3:
            group_regions = random_regions[start_idx:]
        else:
            # Add some variation to group sizes
            variation = random.randint(-1, 1)
            end_idx = start_idx + regions_per_group + variation
            group_regions = random_regions[start_idx:end_idx]
            start_idx = end_idx
        
        # Add group to session state
        st.session_state.custom_groups[name] = group_regions


def display_custom_groups_analysis(df, region_column, value_column, lan_gdf=None):
    """
    Display analysis of custom region groups with comparison table and map visualization.
    
    Args:
        df (pd.DataFrame): DataFrame with processed region data
        region_column (str): Column name with region names
        value_column (str): Column name with values to analyze
        lan_gdf (gpd.GeoDataFrame, optional): GeoDataFrame with län boundaries for map creation
    """
    if not st.session_state.custom_groups:
        st.info("Inga egna regiongrupper har skapats än. Skapa grupper ovan för att se analys.")
        return
    
    # Create grouped data
    grouped_df = create_custom_region_group(
        df, 
        region_column, 
        value_column, 
        st.session_state.custom_groups
    )
    
    if grouped_df.empty:
        st.warning("Kunde inte skapa grupperad data. Kontrollera att de valda regionerna finns i dina data.")
        return
    
    # Display custom regions map if GeoDataFrame is provided
    if lan_gdf is not None:
        st.subheader("Karta över egna regiongrupper")
        
        # Add controls for scale settings
        with st.expander("Skalainställningar", expanded=False):
            use_fixed_scale = st.checkbox("Använd fast skala", value=False)
            
            scale_min = 0
            scale_max = 100
            
            if use_fixed_scale:
                col1, col2 = st.columns(2)
                with col1:
                    scale_min = st.number_input("Minimivärde", value=0.0, step=1.0)
                with col2:
                    scale_max = st.number_input("Maximivärde", value=100.0, step=1.0)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create a container with max width to control the map size
            with st.container():
                # Create the map visualization without borders and patterns
                fig = create_custom_groups_map(
                    df, 
                    lan_gdf, 
                    st.session_state.custom_groups,
                    value_column, 
                    st.session_state.get('color_scheme', 'viridis'),
                    width=st.session_state.get('width', 8),
                    height=st.session_state.get('height', 6),
                    show_borders=False,  # Set to False to remove borders
                    show_labels=False,
                    use_fixed_scale=use_fixed_scale,
                    scale_min=scale_min,
                    scale_max=scale_max
                )
                
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    
                    # Create download button for custom groups map
                    from utils.geo_utils import fig_to_base64
                    img_base64, img_bytes = fig_to_base64(fig)
                    
                    st.markdown("### Ladda ner karta")
                    href = f'<a href="data:image/png;base64,{img_base64}" download="egna_regiongrupper.png" class="download-btn" style="display: inline-block; padding: 0.5rem 1rem; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 0.5rem 0;">⬇️ Ladda ner karta med egna regiongrupper</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
        with col2:
            st.write("Gruppinformation:")
            for group_name, regions in st.session_state.custom_groups.items():
                with st.expander(group_name):
                    st.write(", ".join(regions))
    
    # Display the group comparison table
    st.subheader("Jämförelse av egna regiongrupper")
    st.dataframe(grouped_df.sort_values(value_column, ascending=False))
    
    # Add download button for grouped data
    csv = grouped_df.to_csv(index=False)
    st.download_button(
        label="Ladda ner grupperad data som CSV",
        data=csv,
        file_name="egna_regiongrupper.csv",
        mime="text/csv",
    )
