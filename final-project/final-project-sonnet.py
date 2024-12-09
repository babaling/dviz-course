import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Function to load and preprocess the climate data
def load_climate_data(file_path):
    df = pd.read_csv(file_path)
    # Add preprocessing steps here based on your actual data structure
    return df

# Function to create the base world map
def create_base_map(df):
    fig = go.Figure(data=go.Choropleth(
        locations=df['country_code'],  # Replace with your actual column name
        z=df['temperature'],          # Replace with your actual column name
        text=df['country'],           # Replace with your actual column name
        colorscale='RdBu',
        marker_line_color='darkgray',
        marker_line_width=0.5,
    ))
    
    fig.update_layout(
        title_text='Global Travel Recommendations',
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        ),
        height=600
    )
    return fig

# Function to add markers for recommended destinations
def add_recommendations(fig, recommended_locations):
    fig.add_trace(go.Scattergeo(
        lon=recommended_locations['longitude'],
        lat=recommended_locations['latitude'],
        mode='markers',
        marker=dict(
            size=10,
            color='red',
            symbol='flag'
        ),
        name='Recommended Destinations',
        text=recommended_locations['country'],
        hoverinfo='text'
    ))
    return fig

# Function to filter destinations based on weather preferences
def filter_destinations(df, month, temp_min, temp_max, precip_max):
    mask = (
        (df['month'] == month) &
        (df['temperature'] >= temp_min) &
        (df['temperature'] <= temp_max) &
        (df['precipitation'] <= precip_max)
    )
    return df[mask]

# Main application
def main():
    # Load data
    data_path = Path("all_data_curated_v2.csv")  # Update with your actual path
    climate_data = load_climate_data(data_path)
    
    # Create base map
    fig = create_base_map(climate_data)
    
    # Example: Filter destinations for July with ideal conditions
    recommended = filter_destinations(
        climate_data,
        month=7,
        temp_min=20,
        temp_max=28,
        precip_max=50
    )
    
    # Add recommendations to map
    fig = add_recommendations(fig, recommended)
    
    # Add slider for month selection
    fig.update_layout(
        sliders=[{
            'active': 6,  # July
            'currentvalue': {"prefix": "Month: "},
            'steps': [
                {
                    'label': str(i),
                    'method': "animate",
                    'args': [[str(i)], {
                        'frame': {'duration': 0},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                } for i in range(1, 13)
            ]
        }]
    )
    
    # Show the map
    fig.show()

if __name__ == "__main__":
    main()
    
