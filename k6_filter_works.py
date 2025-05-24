import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta


def load_weather_data(file, file_path=None):
    try:
        if isinstance(file, str) and os.path.exists(file):
            df = pd.read_csv(file)
        else:
            df = pd.read_csv(file)
        if df.empty or 'dt' not in df.columns:
            st.error(f"No valid data or missing dt in {file_path or 'uploaded file'}.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading {file_path or 'uploaded file'}: {e}")
        return None


def filter_weather_data(df, start_timestamp, duration, unit):
    if df is not None and not df.empty:
        if unit == "Hours":
            end_timestamp = start_timestamp + duration * 3600
        elif unit == "Days":
            end_timestamp = start_timestamp + duration * 86400
        else:  # Months
            start_date = datetime.fromtimestamp(start_timestamp)
            end_date = (start_date + pd.offsets.MonthBegin(duration)).timestamp()
            end_timestamp = int(end_date)
        filtered = df[(df['dt'] >= start_timestamp) & (df['dt'] <= end_timestamp)]
        return filtered
    return pd.DataFrame()


def main():
    st.set_page_config(page_title="Weather Visualization", layout="wide")

    # File upload
    st.sidebar.header("Upload CSV Files")
    bern_file = st.sidebar.file_uploader("Bern CSV", type="csv")
    zurich_file = st.sidebar.file_uploader("Zurich CSV", type="csv")

    # Load weather data
    wetter_Bern = None
    wetter_Zurich = None
    default_path_bern = "arbeit/wetter/bern_23_clean.csv"
    default_path_zurich = "arbeit/wetter/zurich_23_clean.csv"

    if bern_file:
        wetter_Bern = load_weather_data(bern_file, "Bern uploaded file")
    elif os.path.exists(default_path_bern):
        wetter_Bern = load_weather_data(default_path_bern, default_path_bern)

    if zurich_file:
        wetter_Zurich = load_weather_data(zurich_file, "Zurich uploaded file")
    elif os.path.exists(default_path_zurich):
        wetter_Zurich = load_weather_data(default_path_zurich, default_path_zurich)

    left, middle = st.columns([1, 3])

    with left:
        st.header("Controls")
        city = st.selectbox("City", ["Bern", "Zurich", "both"])
        month = st.slider("Month", 1, 12, 1)
        day = st.slider("Day", 1, 31, 1)
        hour = st.slider("Hour", 0, 23, 0)
        duration = st.slider("Duration", 1, 100, 26)
        unit = st.selectbox("Unit", ["Hours", "Days", "Months"])

        # Convert inputs to timestamp (2023)
        try:
            start_datetime = datetime(2023, month, day, hour)
            start_timestamp = int(start_datetime.timestamp())
        except ValueError:
            st.error("Invalid date. Adjust month/day/hour (e.g., Feb 30 is invalid).")
            return

        # Select and filter data
        wetter = None
        if city == "Bern" and wetter_Bern is not None:
            wetter = wetter_Bern
        elif city == "Zurich" and wetter_Zurich is not None:
            wetter = wetter_Zurich
        elif city == "both" and wetter_Bern is not None and wetter_Zurich is not None:
            wetter = pd.concat([wetter_Bern, wetter_Zurich])

        if wetter is None:
            st.error(f"No data available for {city}. Check CSV files.")
            filtered_df = pd.DataFrame()
        else:
            filtered_df = filter_weather_data(wetter, start_timestamp, duration, unit)

    with middle:
        st.header("Filtered Weather Data")
        if not filtered_df.empty:
            st.dataframe(filtered_df[['dt', 'dt_iso', 'temp', 'humidity', 'wind_speed', 'weather_description']],
                         use_container_width=True)
        else:
            st.warning("No data available. Check time range or CSV data.")


if __name__ == "__main__":
    main()