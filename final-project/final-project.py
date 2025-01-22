import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data
import urllib.parse  # for URL encoding

#########################
# Initial Setup and Data Preparation
#########################

# Set the page configuration **before** any other Streamlit commands!
st.set_page_config(
    page_title="Global Travel Destination Recommender",
    layout="wide",  # Use a wide layout for better visualization
    initial_sidebar_state="collapsed"  # Start with the sidebar collapsed
)

# Load the dataset from a CSV file with caching for performance
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    return df

df = load_data()

# Disable the maximum row limit for Altair to handle large datasets
alt.data_transformers.disable_max_rows()

# List of climate parameters to consider
param_list = [
    'Precipitation (mm)',
    'Number of Days with Precipitation ≥ 1 mm (#Days)',
    'Mean Daily Maximum Temperature (degC)',
    'Mean Daily Minimum Temperature (degC)',
    'Mean Daily Mean Temperature (degC)',
    'Mean Sea Level Pressure (hPa)',
    'Mean Vapor Pressure (hPa)',
    'Total Number of Hours of Sunshine (Hours)'
]

# List of months for selection
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Load the world map data for the background of the heatmap
world_map = alt.topo_feature(data.world_110m.url, feature="countries")

# Convert the data from wide to long format for easier manipulation
df_long = df.melt(
    id_vars=['Station', 'Country', 'Latitude', 'Longitude', 'Parameter'], 
    var_name='Month', 
    value_name='Value'
)

# Combine Parameter and Month into a single column for pivoting
df_long['Parameter_Month'] = df_long['Parameter'] + '_' + df_long['Month']

# Pivot the long dataframe back to wide format, now with Parameter_Month as columns
df_wide = df_long.pivot_table(
    index=['Station', 'Country', 'Latitude', 'Longitude'], 
    columns='Parameter_Month', 
    values='Value'
).reset_index()

# Remove the hierarchical column index created by pivot_table
df_wide.columns.name = None

# Remove any columns that contain '_Elem' in their name
df_wide = df_wide.loc[:, ~df_wide.columns.str.contains('_Elem')]

# Define default optimal conditions for temperature and precipitation
default_conditions = {
    'Mean Daily Mean Temperature (degC)': (18, 25),  # Optimal temperature range in °C
    'Precipitation (mm)': (0, 50)                    # Optimal precipitation range in mm
}

#########################
# Function Definitions
#########################

def get_min_max(df, param, month):
    """
    Calculate the minimum and maximum values for a specific parameter and month.
    
    Parameters:
    - df: The dataframe containing the data.
    - param: The climate parameter (e.g., 'Precipitation (mm)').
    - month: The month for which to calculate the min and max.
    
    Returns:
    - A tuple containing (min_value, max_value).
    """
    col_name = f"{param}_{month}"
    if col_name in df.columns:
        return float(df[col_name].min()), float(df[col_name].max())
    return None, None

def plot_heatmap(selected_month, filtered_df, chosen_params):
    """
    Generate an Altair heatmap based on the selected month and chosen parameters.
    
    Parameters:
    - selected_month: The month selected by the user.
    - filtered_df: The dataframe filtered based on user inputs.
    - chosen_params: List of parameters selected by the user.
    
    Returns:
    - An Altair chart object representing the heatmap.
    """
    # Define default color and size parameters
    color_param = 'Mean Daily Mean Temperature (degC)'
    size_param = 'Precipitation (mm)'

    # Determine which columns to use for color and size encoding
    color_column = f"{color_param}_{selected_month}"
    size_column = f"{size_param}_{selected_month}"

    # If the default columns are not present, use the first chosen parameter
    if color_column not in filtered_df.columns and len(chosen_params) > 0:
        color_column = f"{chosen_params[0]}_{selected_month}"
    if size_column not in filtered_df.columns and len(chosen_params) > 0:
        size_column = f"{chosen_params[0]}_{selected_month}"

    # Create the background map
    background = alt.Chart(world_map).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project('naturalEarth1').properties(
        width=1000,
        height=600
    )

    # Define the tooltip information to display on hover
    tooltip_list = [
        alt.Tooltip('Station:N', title='Station'),
        alt.Tooltip('Country:N', title='Country'),
        alt.Tooltip('Latitude:Q', title='Latitude'),
        alt.Tooltip('Longitude:Q', title='Longitude')
    ]
    for p in chosen_params:
        col = f"{p}_{selected_month}"
        if col in filtered_df.columns:
            tooltip_list.append(alt.Tooltip(col + ":Q", title=p))

    # Create the heatmap layer with legends
    heatmap = alt.Chart(filtered_df).mark_circle().encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        color=alt.Color(
            color_column, 
            scale=alt.Scale(scheme='viridis'), 
            title='Mean Daily Mean Temperature (degC)',
            legend=alt.Legend(orient='bottom')  # Move color legend to bottom
        ),
        size=alt.Size(
            size_column, 
            title='Precipitation (mm)',
            legend=alt.Legend(orient='bottom')  # Move size legend to bottom
        ),
        tooltip=tooltip_list
    )

    # Combine the background and heatmap, and configure legend font sizes
    chart = (background + heatmap).configure_legend(
        labelFontSize=10,
        titleFontSize=12
    )

    return chart

def add_flags(target_df, selected_month, chosen_params):
    """
    Add red flag markers to the map for locations that meet all filter criteria.
    
    Parameters:
    - target_df: The dataframe containing locations that meet the filter criteria.
    - selected_month: The month selected by the user.
    - chosen_params: List of parameters selected by the user.
    
    Returns:
    - An Altair chart object with red flags.
    """
    # Define the tooltip information for the flags
    tooltip_list = [
        alt.Tooltip('Station:N', title='Station'),
        alt.Tooltip('Country:N', title='Country'),
        alt.Tooltip('Latitude:Q', title='Latitude'),
        alt.Tooltip('Longitude:Q', title='Longitude')
    ]
    for p in chosen_params:
        col = f"{p}_{selected_month}"
        if col in target_df.columns:
            tooltip_list.append(alt.Tooltip(col + ":Q", title=p))

    # Create the flag markers
    points = alt.Chart(target_df).mark_text(text="🚩", size=15, color='red').encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        tooltip=tooltip_list
    )
    return points

#########################
# Streamlit User Interface
#########################

# Initialize dictionaries to hold filter ranges and chosen parameters
filters = {}
chosen_params = []

# Title and Introduction
st.title("🌍 Interactive Global Travel Destination Recommendation")

st.write("""
Welcome to the **Interactive Global Travel Destination Recommendation** tool! This application allows you to explore and identify the best travel destinations around the world based on your preferred climate conditions.

### **How It Works:**
1. **Select a Month:** Choose the month you're planning to travel.
2. **Activate Parameters:** Select the climate parameters that matter most to you.
3. **Adjust Ranges:** Define your ideal range for each activated parameter using the sliders.
4. **View Recommendations:** The map will display countries that meet all your specified criteria, highlighted with red flags.
5. **Explore Further:** Click on the country names to access detailed travel information on [Lonely Planet](https://www.lonelyplanet.com/).

### **Default Optimal Conditions:**
- **Mean Daily Mean Temperature (degC):** 18–25°C
- **Precipitation (mm):** 0–50mm

These defaults are set to represent comfortable and pleasant travel conditions. Feel free to adjust them to match your personal preferences!
""")

st.markdown("---")  # Separator line

# Add subheader for Select Month
st.subheader("📅 **Select Month:**")
# Call selectbox with label and options, hiding the label
selected_month = st.selectbox(
    "",
    options=months,
    index=0,
    label_visibility='collapsed'  # Hide the label for accessibility
)

# Handle slider and map reset when the month changes
if 'last_month' not in st.session_state:
    st.session_state.last_month = selected_month
elif st.session_state.last_month != selected_month:
    # Remove previous month's slider states to reset
    for p in param_list:
        key = f'slider_{p}_{st.session_state.last_month}'
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.last_month = selected_month

# Parameters Selection Section
st.subheader("🔍 **Customize Your Climate Preferences**")
st.write("Select the climate parameters you're interested in and adjust their ranges to find your ideal travel destinations.")

# Organize checkboxes within a single container
with st.expander("📋 **Select Climate Parameters:**", expanded=True):
    # Use Streamlit's columns to arrange checkboxes neatly
    num_columns = 4  
    cols = st.columns(num_columns)
    
    for idx, p in enumerate(param_list):
        with cols[idx % num_columns]:
            # Determine if the parameter should be checked by default
            default_check = (p in default_conditions)
            use_param = st.checkbox(p, value=default_check, key=f"check_{p}")
            if use_param:
                chosen_params.append(p)

# Display sliders only for selected parameters
if chosen_params:
    st.write("### 📏 **Adjust Climate Parameters Ranges:**")
    for p in chosen_params:
        # Calculate the minimum and maximum values for the current parameter and month
        param_min, param_max = get_min_max(df_wide, p, selected_month)
        if param_min is not None and param_max is not None:
            if p in default_conditions:
                # Apply default optimal conditions within the data's range
                default_low, default_high = default_conditions[p]
                default_low = max(param_min, default_low)
                default_high = min(param_max, default_high)
            else:
                default_low, default_high = param_min, param_max

            # Define a unique key for each slider based on parameter and month
            slider_key = f'slider_{p}_{selected_month}'

            # Define the default range for the slider
            slider_default = (float(default_low), float(default_high))

            # Create the slider with consistent float types
            user_range = st.slider(
                f"**{p}:**",
                float(param_min),
                float(param_max),
                slider_default,
                key=slider_key
            )

            # Add the selected range to the filters dictionary
            filters[p] = user_range
else:
    st.info("✅ **Select at least one climate parameter to see corresponding sliders and recommendations.**")

st.markdown("---")  # Separator line

# Apply the filters to the dataframe
filtered = df_wide.copy()
for p, (low, high) in filters.items():
    col_name = f"{p}_{selected_month}"
    filtered = filtered[(filtered[col_name] >= low) & (filtered[col_name] <= high)]

# Visualization Section
st.subheader("📊 **Climate Conditions Map**")
st.write("The map below highlights countries that match your specified climate preferences. Countries meeting all criteria are marked with red flags.")

# Generate the heatmap based on the filtered data
base_chart = plot_heatmap(selected_month, df_wide, chosen_params)

# Add flags for the filtered countries
flag_chart = add_flags(filtered, selected_month, chosen_params)

# Combine the heatmap and flags into one chart
combined_chart = base_chart + flag_chart

# Display the combined chart in Streamlit
st.altair_chart(combined_chart, use_container_width=True)

# Results Section
st.subheader("📝 **Your Ideal Countries:**")
st.write("Below is a table of countries that meet your climate preferences. Click on a country name to explore more about traveling there.")

# Define columns to display
display_cols = ['Station', 'Country', 'Latitude', 'Longitude']
for p in chosen_params:
    col_name = f"{p}_{selected_month}"
    if col_name in df_wide.columns:
        display_cols.append(col_name)

# Display the filtered countries in a table
st.dataframe(filtered[display_cols])

# **Display the list of country names with clickable links**
st.subheader("🌐 **List of Countries:**")
st.write("Explore detailed travel information for each country by clicking on their names below:")

# Extract unique country names and sort them
countries = filtered['Country'].unique()
sorted_countries = sorted(countries)

# A bulleted list of countries with clickable links using Markdown
# Each link directs to Lonely Planet's search page for the respective country
country_links = [
    f"- [{country}](https://www.lonelyplanet.com/search?places%5Bquery%5D={urllib.parse.quote_plus(country)})" 
    for country in sorted_countries
]
st.markdown('\n'.join(country_links))

st.markdown("---")

# Additional Information Section
st.write("""
### 🔍 **Data Sources**
- **Climate Data:** [WMO Climate Normals from NCEI](https://www.ncei.noaa.gov/products/wmo-climate-normals)
- **World Map Data:** [Vega Datasets](https://github.com/vega/vega-datasets)

### 📧 **Contact**
For any questions or feedback, feel free to reach out at [shinjih@iu.edu](mailto:shinjih@iu.edu).
""")