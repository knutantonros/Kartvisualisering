import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import json
import requests
from io import BytesIO
import base64
from shapely.geometry import shape, MultiPolygon, Polygon
import geopandas as gpd
from matplotlib.cm import get_cmap
import os

# Set page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="Visualiseringsverktyg för Svenska Regioner", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "En visualiseringsapp för svenska läns- och NUTS-2-data"
    }
)

# Title and description
st.title("Visualiseringsverktyg för Svenska Regioner")
st.markdown("Ladda upp dina data och visualisera dem efter svenska län eller NUTS-2-regioner.")

# Add CSS for responsive layout
st.markdown("""
""", unsafe_allow_html=False)

# Define the mapping between län codes and names
LAN_MAPPING = {
    '01': 'Stockholm',
    '03': 'Uppsala',
    '04': 'Södermanland',
    '05': 'Östergötland',
    '06': 'Jönköping',
    '07': 'Kronoberg',
    '08': 'Kalmar',
    '09': 'Gotland',
    '10': 'Blekinge',
    '12': 'Skåne',
    '13': 'Halland',
    '14': 'Västra Götaland',
    '17': 'Värmland',
    '18': 'Örebro',
    '19': 'Västmanland',
    '20': 'Dalarna',
    '21': 'Gävleborg',
    '22': 'Västernorrland',
    '23': 'Jämtland',
    '24': 'Västerbotten',
    '25': 'Norrbotten'
}

# Define mapping between län and NUTS-2 regions
NUTS2_MAPPING = {
    'Stockholm': 'SE11 Stockholm',
    'Uppsala': 'SE12 Östra Mellansverige',
    'Södermanland': 'SE12 Östra Mellansverige',
    'Östergötland': 'SE12 Östra Mellansverige',
    'Örebro': 'SE12 Östra Mellansverige',
    'Västmanland': 'SE12 Östra Mellansverige',
    'Jönköping': 'SE21 Småland med öarna',
    'Kronoberg': 'SE21 Småland med öarna',
    'Kalmar': 'SE21 Småland med öarna',
    'Gotland': 'SE21 Småland med öarna',
    'Blekinge': 'SE22 Sydsverige',
    'Skåne': 'SE22 Sydsverige',
    'Halland': 'SE23 Västsverige',
    'Västra Götaland': 'SE23 Västsverige',
    'Värmland': 'SE31 Norra Mellansverige',
    'Dalarna': 'SE31 Norra Mellansverige',
    'Gävleborg': 'SE31 Norra Mellansverige',
    'Västernorrland': 'SE32 Mellersta Norrland',
    'Jämtland': 'SE32 Mellersta Norrland',
    'Västerbotten': 'SE33 Övre Norrland',
    'Norrbotten': 'SE33 Övre Norrland'
}

# Function to create sample data
def create_sample_data():
    """Create a sample dataset for demonstration"""
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

@st.cache_data
def load_geojson():
    """Load GeoJSON files for Swedish län and NUTS-2 regions"""
    try:
        # Load Swedish län GeoJSON
        lan_url = "https://raw.githubusercontent.com/okfse/sweden-geojson/master/swedish_regions.geojson"
        lan_response = requests.get(lan_url)
        lan_geojson = lan_response.json()
        lan_gdf = gpd.GeoDataFrame.from_features(lan_geojson["features"])
        
        # Download Eurostat NUTS-2 GeoJSON for Sweden
        nuts2_url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_60M_2021_3035_LEVL_2.geojson"
        nuts2_response = requests.get(nuts2_url)
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
            nuts_id_to_name = {
                'SE11': 'Stockholm',
                'SE12': 'Östra Mellansverige',
                'SE21': 'Småland med öarna',
                'SE22': 'Sydsverige',
                'SE23': 'Västsverige',
                'SE31': 'Norra Mellansverige',
                'SE32': 'Mellersta Norrland',
                'SE33': 'Övre Norrland'
            }
            if 'NUTS_ID' in nuts2_gdf.columns:
                nuts2_gdf['name'] = nuts2_gdf['NUTS_ID'].map(nuts_id_to_name)
            else:
                st.warning("Could not find appropriate columns in NUTS-2 GeoJSON. Visualization may not work correctly.")
        
        return lan_gdf, nuts2_gdf
    
    except Exception as e:
        st.error(f"Error loading GeoJSON data: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
def process_data(df, region_column, value_column):
    """Process the uploaded data to prepare it for visualization"""
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
        
        # Aggregate by län and NUTS-2 if needed
        lan_data = processed_df.groupby('region_name')[value_column].mean().reset_index()
        nuts2_data = nuts2_data.groupby('nuts2_region')[value_column].mean().reset_index()
        
        # Handle empty dataframes
        if len(lan_data) == 0 and len(nuts2_data) == 0:
            st.error("No valid data to visualize after processing. Check your input data.")
            return pd.DataFrame(), pd.DataFrame()
        
        return lan_data, nuts2_data
    except Exception as e:
        st.error(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame()

def create_matplotlib_map(data, gdf, location_col, value_column, color_scheme, width=8, height=6, is_nuts2=False):
    """
    Create a choropleth map of Sweden using matplotlib with NUTS-2 and Län support
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
        
        # Plot the regions with white border lines
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
        import traceback
        print(traceback.format_exc())
        return None

def fig_to_base64(fig):
    """Convert a matplotlib figure to base64 string with optimized settings"""
    buf = BytesIO()
    # Use more compatible parameters without optimize/compression
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='#E6E6E6', transparent=False, pad_inches=0)
    buf.seek(0)
    img_bytes = buf.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode()
    buf.close()
    return img_base64, img_bytes

def create_visualization(lan_data, nuts2_data, lan_gdf, nuts2_gdf, map_type, value_column, color_scheme, width=8, height=6):
    """Create and display the visualization with a more reasonable default size"""
    try:
        st.header(f"Visualisering")
        
        # Determine which data to use
        is_nuts2 = False
        if map_type == "Län" and not lan_data.empty:
            gdf = lan_gdf
            data = lan_data
            location_col = 'region_name'
        elif not nuts2_data.empty:
            gdf = nuts2_gdf
            data = nuts2_data
            location_col = 'nuts2_region'
            is_nuts2 = True
        else:
            st.error("Inga data tillgängliga för visualisering.")
            return
        
        # Use a container with max width to control the map size
        with st.container():
            # Create the matplotlib visualization
            fig = create_matplotlib_map(data, gdf, location_col, value_column, color_scheme, width, height, is_nuts2)
            
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
                    file_name=f"{'lan' if map_type == 'Län' else 'nuts2'}_bearbetade_data.csv",
                    mime="text/csv",
                )
    except Exception as e:
        st.error(f"Fel vid skapande av visualisering: {e}")
        print(e)  # Also print to console for debugging

def main():
    # Load GeoJSON data as GeoDataFrames
    lan_gdf, nuts2_gdf = load_geojson()
    
    # Sidebar for user inputs
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
            st.header("Kartinställningar")
            
            # Determine possible region columns
            possible_region_cols = [col for col in df.columns if any(x in col.lower() for x in ['lan', 'län', 'region', 'county', 'code', 'kod', 'namn'])]
            default_region_col = possible_region_cols[0] if possible_region_cols else df.columns[0]
            
            region_column = st.selectbox(
                "Välj kolumnen med länsnamn eller länskoder:", 
                df.columns,
                index=df.columns.get_loc(default_region_col) if default_region_col in df.columns else 0
            )
            
            # Filter out the region column and non-numeric columns for value selection
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                value_column = st.selectbox("Välj kolumnen med värden att visualisera:", numeric_cols)
            else:
                value_column = st.selectbox("Välj kolumnen med värden att visualisera:", 
                                         [col for col in df.columns if col != region_column])
            
            # Color scheme
            color_scheme = st.selectbox("Välj färgschema:", 
                                       ["viridis", "Blues", "Reds", "Greens", "YlOrRd", "Spectral", "plasma", "inferno", "magma", "cividis"])
            
            # Map type selection
            map_type = st.radio("Välj visualiseringsnivå:", ["Län", "NUTS-2 Regioner"])
            
            # Map size controls
            st.subheader("Diagramyta")
            
            # Size presets first (so they can override sliders)
            size_preset = st.radio(
                "Förinställd storlek:",
                ["Liten (6x4)", "Medium (8x6)", "Stor (12x8)", "Anpassad"]
            )
            
            # Default values for the sliders based on preset
            if size_preset == "Liten (6x4)":
                width_default, height_default = 6, 4
            elif size_preset == "Medium (8x6)":
                width_default, height_default = 8, 6
            elif size_preset == "Stor (12x8)":
                width_default, height_default = 12, 8
            else:  # Anpassad
                width_default, height_default = 8, 6
            
            # Show sliders only if "Anpassad" is selected
            if size_preset == "Anpassad":
                width = st.slider("Bredd", min_value=4, max_value=16, value=width_default, step=1)
                height = st.slider("Höjd", min_value=3, max_value=12, value=height_default, step=1)
            else:
                width, height = width_default, height_default
            
            # Process button
            if st.button("Generera visualisering"):
                with st.spinner("Bearbetar data och skapar visualisering..."):
                    lan_data, nuts2_data = process_data(df, region_column, value_column)
                    
                    if not lan_data.empty or not nuts2_data.empty:
                        st.session_state['lan_data'] = lan_data
                        st.session_state['nuts2_data'] = nuts2_data
                        st.session_state['map_type'] = map_type
                        st.session_state['value_column'] = value_column
                        st.session_state['color_scheme'] = color_scheme
                        st.session_state['width'] = width
                        st.session_state['height'] = height
                        st.session_state['visualization_ready'] = True
                    else:
                        st.error("Kunde inte bearbeta data för visualisering.")
    
    # Main content area - display info message if no data
    if 'visualization_ready' not in st.session_state or not st.session_state['visualization_ready']:
        st.info("Välj dataalternativ och klicka på 'Generera visualisering' för att börja.")
        
        # Sample data format
        st.header("Om denna app")
        st.markdown("""
        Denna app låter dig visualisera data över svenska regioner, antingen efter:
        - **Län**: Sveriges 21 län
        - **NUTS-2 Regioner**: Europeiska statistiska regioner (8 regioner i Sverige)
        
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
    else:
        # Create visualization based on processed data
        create_visualization(
            st.session_state['lan_data'],
            st.session_state['nuts2_data'],
            lan_gdf,
            nuts2_gdf,
            st.session_state['map_type'],
            st.session_state['value_column'], 
            st.session_state['color_scheme'],
            st.session_state['width'],  # Use the width from session state
            st.session_state['height']  # Use the height from session state
        )

if __name__ == "__main__":
    main()