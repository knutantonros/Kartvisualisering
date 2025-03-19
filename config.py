"""
Configuration settings and constants for the Swedish regions visualization app.
"""

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

# URL settings
LAN_GEOJSON_URL = "https://raw.githubusercontent.com/okfse/sweden-geojson/master/swedish_regions.geojson"
NUTS2_GEOJSON_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_60M_2021_3035_LEVL_2.geojson"

# NUTS2 ID to name mapping (fallback)
NUTS_ID_TO_NAME = {
    'SE11': 'Stockholm',
    'SE12': 'Östra Mellansverige',
    'SE21': 'Småland med öarna',
    'SE22': 'Sydsverige',
    'SE23': 'Västsverige',
    'SE31': 'Norra Mellansverige',
    'SE32': 'Mellersta Norrland',
    'SE33': 'Övre Norrland'
}

# App settings
APP_TITLE = "Visualiseringsverktyg för Svenska Regioner"
APP_DESCRIPTION = "Ladda upp dina data och visualisera dem efter svenska län eller NUTS-2-regioner."
APP_ABOUT = "En visualiseringsapp för svenska läns- och NUTS-2-data"

# Color schemes
COLOR_SCHEMES = ["viridis", "Blues", "Reds", "Greens", "YlOrRd", "Spectral", "plasma", "inferno", "magma", "cividis"]

# Size presets
SIZE_PRESETS = {
    "Liten (6x4)": (6, 4),
    "Medium (8x6)": (8, 6),
    "Stor (12x8)": (12, 8),
    "Anpassad": None
}