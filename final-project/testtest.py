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

# 데이터를 long format으로 변환
df_long = df.melt(id_vars=['Station', 'Country', 'Latitude', 'Longitude', 'Parameter'], 
                  var_name='Month', value_name='Value')

# 각 행의 Parameter와 Month를 합쳐서 새로운 컬럼 이름 생성
df_long['Parameter_Month'] = df_long['Parameter'] + '_' + df_long['Month']

# 데이터를 wide format으로 변환
df_wide = df_long.pivot_table(index=['Station', 'Country', 'Latitude', 'Longitude'], 
                              columns='Parameter_Month', values='Value').reset_index()

df_wide.columns.name = None  # 컬럼 이름의 이름 제거

# 'Elem' 열 제거
df_wide = df_wide.loc[:, ~df_wide.columns.str.contains('_Elem')]

# 기본 최적 조건
default_conditions = {
    'Mean Daily Mean Temperature (degC)': (18, 25),
    'Precipitation (mm)': (0, 50)
}

#########################
# 함수 정의
#########################

def get_min_max(df, param, month):
    """특정 Parameter와 월에 대해 최소/최대값 계산"""
    col_name = f"{param}_{month}"
    if col_name in df.columns:
        return float(df[col_name].min()), float(df[col_name].max())
    return None, None

def plot_heatmap(selected_month, filtered_df, chosen_params):
    """Heatmap 생성"""
    color_param = 'Mean Daily Mean Temperature (degC)'
    size_param = 'Precipitation (mm)'

    color_column = f"{color_param}_{selected_month}"
    size_column = f"{size_param}_{selected_month}"

    if color_column not in filtered_df.columns and len(chosen_params) > 0:
        color_column = f"{chosen_params[0]}_{selected_month}"
    if size_column not in filtered_df.columns and len(chosen_params) > 0:
        size_column = f"{chosen_params[0]}_{selected_month}"

    background = alt.Chart(world_map).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project('naturalEarth1').properties(
        width=1000,
        height=600
    )

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

    heatmap = alt.Chart(filtered_df).mark_circle().encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        color=alt.Color(color_column, scale=alt.Scale(scheme='viridis'), title='Mean degC'),
        size=alt.Size(size_column, title='Intensity'),
        tooltip=tooltip_list
    )

    chart = (background + heatmap).configure_legend(
        labelFontSize=10,
        titleFontSize=12
    )

    return chart

def add_flags(target_df, selected_month, chosen_params):
    """조건을 만족하는 깃발 추가"""
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

    points = alt.Chart(target_df).mark_text(text="🚩", size=15, color='red').encode(
        longitude='Longitude:Q',
        latitude='Latitude:Q',
        tooltip=tooltip_list
    )
    return points

#########################
# Streamlit UI
#########################

st.title("Interactive Global Travel Destination Recommendation")

st.write("""
이 대화형 시각화는 월별로 전세계 기후 조건을 확인하고, 사용자가 설정한 이상적 기후 범위에 맞는 여행지를 추천합니다.  
- 상단에서 월을 선택하면 기본 최적 조건으로 필터링  
- 다른 파라미터를 체크하고 슬라이더로 범위를 변경하여 여행지를 탐색  
- 모든 조건을 만족하는 국가에만 지도에 빨간 깃발 표시  
- 월을 바꿀 때마다 슬라이더와 지도가 초기화됩니다.
""")

selected_month = st.selectbox("Select Month:", months, index=0)

# 월 변경 감지 및 슬라이더 초기화
if 'last_month' not in st.session_state:
    st.session_state.last_month = selected_month
elif st.session_state.last_month != selected_month:
    # 이전 월의 슬라이더 상태 삭제
    for p in param_list:
        key = f"slider_{p}_{st.session_state.last_month}"
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.last_month = selected_month

filters = {}
chosen_params = []

for p in param_list:
    param_min, param_max = get_min_max(df_wide, p, selected_month)
    if param_min is not None and param_max is not None:
        default_check = (p in default_conditions)
        use_param = st.checkbox(p, value=default_check, key=f"check_{p}")
        if use_param:
            chosen_params.append(p)
            if p in default_conditions:
                default_low, default_high = default_conditions[p]
                # 슬라이더의 기본 범위를 데이터 범위 내로 조정
                default_low = max(param_min, default_low)
                default_high = min(param_max, default_high)
            else:
                default_low, default_high = param_min, param_max

            # 슬라이더의 고유 키 정의 (파라미터와 월을 포함)
            slider_key = f'slider_{p}_{selected_month}'

            # 슬라이더의 기본 값 정의
            slider_default = (float(default_low), float(default_high))

            # 슬라이더 생성 (슬라이더는 스트림릿이 자동으로 session_state 관리)
            user_range = st.slider(
                f"Select range for {p} ({selected_month}):",
                float(param_min),
                float(param_max),
                slider_default,
                key=slider_key
            )

            # 슬라이더 값 필터에 추가
            filters[p] = user_range

# 데이터 필터링
filtered = df_wide.copy()
for p, (low, high) in filters.items():
    col_name = f"{p}_{selected_month}"
    filtered = filtered[(filtered[col_name] >= low) & (filtered[col_name] <= high)]

# 차트 생성
base_chart = plot_heatmap(selected_month, df_wide, chosen_params)
flag_chart = add_flags(filtered, selected_month, chosen_params)
combined_chart = base_chart + flag_chart

# 차트 표시
st.altair_chart(combined_chart, use_container_width=True)

# 필터링된 결과 테이블 표시
st.write("**Filtered Countries:**")
display_cols = ['Station', 'Country', 'Latitude', 'Longitude']
for p in chosen_params:
    col_name = f"{p}_{selected_month}"
    if col_name in df_wide.columns:
        display_cols.append(col_name)

st.dataframe(filtered[display_cols])
