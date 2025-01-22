import pandas as pd
import altair as alt
import streamlit as st
from vega_datasets import data

#########################
# 초기 설정 및 데이터 준비
#########################
df = pd.read_csv('data.csv')
alt.data_transformers.disable_max_rows()

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

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
world_map = alt.topo_feature(data.world_110m.url, feature="countries")

# 기본 최적 조건
default_conditions = {
    'Mean Daily Mean Temperature (degC)': (18, 25),
    'Precipitation (mm)': (0, 50)
}

#########################
# 함수 정의
#########################

def calculate_min_max(df, selected_param, selected_month):
    """특정 Parameter와 월에 대해 최소/최대값 계산"""
    filtered = df[df['Parameter'] == selected_param]
    min_val = filtered[selected_month].min()
    max_val = filtered[selected_month].max()
    return float(min_val), float(max_val)

def plot_heatmap(filtered_df, selected_param, selected_month):
    """Heatmap 생성"""
    background = alt.Chart(world_map).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project('naturalEarth1').properties(
        width=1000,
        height=600
    )

    heatmap = alt.Chart(filtered_df).mark_circle().encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        color=alt.Color(f'{selected_month}:Q', scale=alt.Scale(scheme='viridis'), title=selected_param),
        size=alt.Size(f'{selected_month}:Q', title='Value'),
        tooltip=[
            'Station:N',
            'Country:N',
            'Latitude:Q',
            'Longitude:Q',
            alt.Tooltip(f'{selected_month}:Q', title=selected_param)
        ]
    )
    return background + heatmap

def add_flags(df, selected_param, selected_month, value_range):
    """조건을 만족하는 깃발 추가"""
    min_val, max_val = value_range
    filtered = df[
        (df['Parameter'] == selected_param) &
        (df[selected_month] >= min_val) &
        (df[selected_month] <= max_val)
    ]
    flags = alt.Chart(filtered).mark_text(text="🚩", size=15, color='red').encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        tooltip=[
            'Station:N',
            'Country:N',
            'Latitude:Q',
            'Longitude:Q',
            alt.Tooltip(f'{selected_month}:Q', title=selected_param)
        ]
    )
    return flags, filtered

#########################
# Streamlit UI
#########################

st.title("Interactive Global Travel Destination Recommendation")

st.write("""
이 대화형 시각화는 월별로 전세계 기후 조건을 확인하고, 사용자가 설정한 이상적 기후 범위에 맞는 여행지를 추천합니다.
""")

# Parameter 및 월 선택
selected_param = st.selectbox("Select Parameter:", param_list)
selected_month = st.selectbox("Select Month:", months)

# 슬라이더 범위 계산
param_min, param_max = calculate_min_max(df, selected_param, selected_month)

# 슬라이더 표시 및 값 선택
value_range = st.slider(
    f"Select range for {selected_param} ({selected_month}):",
    float(param_min),
    float(param_max),
    (float(param_min), float(param_max))
)

# 조건에 맞는 데이터 필터링
flags_chart, filtered_df = add_flags(df, selected_param, selected_month, value_range)

# Heatmap 및 깃발 표시
heatmap_chart = plot_heatmap(filtered_df, selected_param, selected_month)
combined_chart = heatmap_chart + flags_chart
st.altair_chart(combined_chart, use_container_width=True)

# 필터링된 결과 테이블 표시
st.write("**Filtered Results:**")
st.dataframe(filtered_df[['Station', 'Country', 'Latitude', 'Longitude', selected_month]])
