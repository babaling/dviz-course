import pandas as pd
import streamlit as st
import plotly.express as px

# Streamlit 애플리케이션 제목
st.title("Monthly Overseas Travel Destination Recommendations")

# 데이터 파일 리스트
data_files = [
    'data/wmo_normals_9120_DP01.csv',
    'data/wmo_normals_9120_MNVP.csv',
    'data/wmo_normals_9120_MSLP.csv',
    'data/wmo_normals_9120_PRCP.csv',
    'data/wmo_normals_9120_TAVG.csv',
    'data/wmo_normals_9120_TMAX.csv',
    'data/wmo_normals_9120_TMIN.csv',
    'data/wmo_normals_9120_TSUN.csv'
]

# 데이터프레임 리스트
dataframes = []

# 데이터 로드 및 기본 정보 표시
st.header("1. 데이터 로드 및 공통 컬럼 확인")
for file in data_files:
    try:
        df = pd.read_csv(file)
        st.write(f"### {file} DataFrame")
        st.write(df.head())
        dataframes.append(df)
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {file}")
    except Exception as e:
        st.error(f"파일 로드 중 오류가 발생했습니다: {file}. 오류: {e}")

# 모든 데이터프레임의 컬럼 찾기
common_columns = set(dataframes[0].columns)
for df in dataframes[1:]:
    common_columns = common_columns.intersection(set(df.columns))

st.write(f"**모든 파일에 공통으로 존재하는 컬럼:** {common_columns}")

if not common_columns:
    st.error("공통으로 존재하는 컬럼이 없습니다. 데이터 파일을 확인해주세요.")
    st.stop()

# 공통 컬럼 리스트
common_columns = list(common_columns)

# 병합할 데이터프레임 리스트 (필요한 컬럼만 선택)
merged_df = dataframes[0][common_columns].copy()

for df in dataframes[1:]:
    # 현재 데이터프레임에서 공통 컬럼만 선택
    df_common = df[common_columns].copy()
    
    # 병합
    merged_df = pd.merge(merged_df, df_common, on=common_columns, how='inner')

st.header("2. 병합된 데이터프레임 확인")
st.write(f"Merged DataFrame Shape: {merged_df.shape}")
st.write(merged_df.head())

# 공통 컬럼 중 월 정보가 있는지 확인
if 'Month' not in merged_df.columns:
    st.error("'Month' 컬럼이 존재하지 않습니다. 데이터를 확인해주세요.")
    st.stop()

# 월을 숫자로 매핑
month_map = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
            'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}

merged_df['Month_num'] = merged_df['Month'].map(month_map)

# 필요한 컬럼 선택 및 NaN 제거
required_columns = ['Latitude', 'Longitude', 'Country', 'Station', 'Month_num', 
                    'TMAX', 'TMIN', 'TAVG', 'PRCP', 'MNVP', 'DP01', 'TSUN', 'MSLP']

# 존재하지 않는 컬럼이 있는지 확인
missing_required = [col for col in required_columns if col not in merged_df.columns]
if missing_required:
    st.error(f"필수 컬럼이 누락되었습니다: {missing_required}")
    st.stop()

merged_df = merged_df[required_columns].dropna()

# 데이터 타입 변환
numeric_columns = ['TMAX', 'TMIN', 'TAVG', 'PRCP', 'MNVP', 'DP01', 'TSUN', 'MSLP']
merged_df[numeric_columns] = merged_df[numeric_columns].astype(float)

# 데이터 검증
st.header("3. 데이터 검증")
if merged_df['TMAX'].isnull().any():
    st.error("Error: 'TMAX' column contains NaN values after cleaning.")
    st.stop()
else:
    st.success("'TMAX' column is clean. No NaN values present.")

# 데이터 검증을 위한 추가 출력
st.write("Merged DataFrame contains NaN values:")
st.write(merged_df.isnull().sum())

st.write("Merged DataFrame head:")
st.write(merged_df.head())

# 필터 선택 인터페이스
st.header("4. 필터 선택 및 슬라이더 설정")

# 사용 가능한 필터 목록
available_filters = ['Month', 'TMAX', 'TMIN', 'TAVG', 'PRCP', 'MNVP', 'DP01', 'TSUN', 'MSLP']

# 체크박스를 사용하여 필터 선택
selected_filters = []
for filt in available_filters:
    if st.checkbox(f"Filter by {filt}"):
        selected_filters.append(filt)

# 선택된 필터에 따라 슬라이더 생성
filter_values = {}

if 'Month' in selected_filters:
    # 월 필터는 범위가 아닌 단일 값 선택
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = st.select_slider(
        "Select Month",
        options=list(range(1, 13)),
        value=7,
        format_func=lambda x: f"{x} - {month_names[x-1]}"
    )
    filter_values['Month_num'] = month

if 'TMAX' in selected_filters:
    tmax_min = int(merged_df['TMAX'].min())
    tmax_max = int(merged_df['TMAX'].max())
    tmax_range = st.slider(
        "Temperature Range (°C)",
        min_value=tmax_min,
        max_value=tmax_max,
        value=(int(merged_df['TMAX'].quantile(0.25)), int(merged_df['TMAX'].quantile(0.75))),
        step=1
    )
    filter_values['TMAX_min'] = tmax_range[0]
    filter_values['TMAX_max'] = tmax_range[1]

if 'TMIN' in selected_filters:
    tmin_min = int(merged_df['TMIN'].min())
    tmin_max = int(merged_df['TMIN'].max())
    tmin_range = st.slider(
        "Minimum Temperature Range (°C)",
        min_value=tmin_min,
        max_value=tmin_max,
        value=(int(merged_df['TMIN'].quantile(0.25)), int(merged_df['TMIN'].quantile(0.75))),
        step=1
    )
    filter_values['TMIN_min'] = tmin_range[0]
    filter_values['TMIN_max'] = tmin_range[1]

if 'TAVG' in selected_filters:
    tavg_min = int(merged_df['TAVG'].min())
    tavg_max = int(merged_df['TAVG'].max())
    tavg_range = st.slider(
        "Average Temperature Range (°C)",
        min_value=tavg_min,
        max_value=tavg_max,
        value=(int(merged_df['TAVG'].quantile(0.25)), int(merged_df['TAVG'].quantile(0.75))),
        step=1
    )
    filter_values['TAVG_min'] = tavg_range[0]
    filter_values['TAVG_max'] = tavg_range[1]

if 'PRCP' in selected_filters:
    prcp_min = int(merged_df['PRCP'].min())
    prcp_max = int(merged_df['PRCP'].max())
    prcp_range = st.slider(
        "Precipitation Range (mm)",
        min_value=prcp_min,
        max_value=prcp_max,
        value=(int(merged_df['PRCP'].quantile(0.25)), int(merged_df['PRCP'].quantile(0.75))),
        step=10
    )
    filter_values['PRCP_min'] = prcp_range[0]
    filter_values['PRCP_max'] = prcp_range[1]

if 'MNVP' in selected_filters:
    mnvp_min = int(merged_df['MNVP'].min())
    mnvp_max = int(merged_df['MNVP'].max())
    mnvp_range = st.slider(
        "Vapor Pressure Range (hPa)",
        min_value=mnvp_min,
        max_value=mnvp_max,
        value=(int(merged_df['MNVP'].quantile(0.25)), int(merged_df['MNVP'].quantile(0.75))),
        step=1
    )
    filter_values['MNVP_min'] = mnvp_range[0]
    filter_values['MNVP_max'] = mnvp_range[1]

if 'DP01' in selected_filters:
    dp01_min = int(merged_df['DP01'].min())
    dp01_max = int(merged_df['DP01'].max())
    dp01_range = st.slider(
        "DP01 Range",
        min_value=dp01_min,
        max_value=dp01_max,
        value=(int(merged_df['DP01'].quantile(0.25)), int(merged_df['DP01'].quantile(0.75))),
        step=1
    )
    filter_values['DP01_min'] = dp01_range[0]
    filter_values['DP01_max'] = dp01_range[1]

if 'TSUN' in selected_filters:
    tsun_min = int(merged_df['TSUN'].min())
    tsun_max = int(merged_df['TSUN'].max())
    tsun_range = st.slider(
        "TSUN Range",
        min_value=tsun_min,
        max_value=tsun_max,
        value=(int(merged_df['TSUN'].quantile(0.25)), int(merged_df['TSUN'].quantile(0.75))),
        step=1
    )
    filter_values['TSUN_min'] = tsun_range[0]
    filter_values['TSUN_max'] = tsun_range[1]

if 'MSLP' in selected_filters:
    mslp_min = int(merged_df['MSLP'].min())
    mslp_max = int(merged_df['MSLP'].max())
    mslp_range = st.slider(
        "MSLP Range",
        min_value=mslp_min,
        max_value=mslp_max,
        value=(int(merged_df['MSLP'].quantile(0.25)), int(merged_df['MSLP'].quantile(0.75))),
        step=1
    )
    filter_values['MSLP_min'] = mslp_range[0]
    filter_values['MSLP_max'] = mslp_range[1]