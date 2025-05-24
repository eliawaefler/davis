import folium
import pandas as pd
import streamlit as st
import random
from datetime import datetime, timedelta
from pyproj import Transformer
import plotly.express as px
import numpy as np
import os


def swiss_to_wgs84(easting, northing):
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting, northing)
    return [lat, lon]


def display_map(city_coords, points, zoom=13):
    m = folium.Map(
        location=city_coords,
        zoom_start=zoom,
        tiles="cartodbpositron",
        attr="",
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False
    )
    for point in points:
        if isinstance(point, dict) and "coords" in point and "color" in point:
            folium.CircleMarker(
                location=point["coords"],
                radius=5,
                color=point["color"],
                fill=True,
                fill_color=point["color"]
            ).add_to(m)
    return m


def load_weather_data(file, file_path=None):
    try:
        if isinstance(file, str) and os.path.exists(file):
            df = pd.read_csv(file)
        else:
            df = pd.read_csv(file)

        if df.empty or 'dt_iso' not in df.columns:
            st.error(f"No valid data or missing dt_iso in {file_path or 'uploaded file'}.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading {file_path or 'uploaded file'}: {e}")
        return None


def filter_weather_data(df, start_datetime, end_datetime):
    if df is not None and not df.empty:
        start_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        df['dt_iso_clean'] = df['dt_iso'].str.replace(' +0000 UTC', '', regex=True)
        filtered = df[(df['dt_iso_clean'] >= start_str) & (df['dt_iso_clean'] <= end_str)]
        return filtered.drop(columns=['dt_iso_clean'], errors='ignore')
    return pd.DataFrame()


def get_representative_weather(df, start_datetime, end_datetime, max_points=10):
    if df.empty:
        return df
    timespan_hours = (end_datetime - start_datetime).total_seconds() / 3600
    timespan_days = (end_datetime.date() - start_datetime.date()).days + 1

    df['dt_iso_clean'] = pd.to_datetime(df['dt_iso'].str.replace(' +0000 UTC', '', regex=True),
                                        format='%Y-%m-%d %H:%M:%S', errors='coerce')

    if timespan_days > 1:
        df['date'] = df['dt_iso_clean'].dt.date
        daily = df.groupby('date').agg({
            'temp': 'mean',
            'humidity': 'mean',
            'wind_speed': 'mean',
            'weather_icon': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
            'weather_description': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
        }).reset_index()
        daily['dt_iso'] = pd.to_datetime(daily['date'])
        if len(daily) > max_points:
            indices = np.linspace(0, len(daily) - 1, max_points, dtype=int)
            daily = daily.iloc[indices]
        return daily
    elif timespan_hours > 10:
        filtered = df.iloc[::2]
        if len(filtered) > max_points:
            indices = np.linspace(0, len(filtered) - 1, max_points, dtype=int)
            filtered = filtered.iloc[indices]
        return filtered
    else:
        if len(df) > max_points:
            indices = np.linspace(0, len(df) - 1, max_points, dtype=int)
            df = df.iloc[indices]
        return df


def get_weather_emoji(weather_icon):
    emoji_map = {
        '01d': ':sunny:',  # clear sky (day)
        '01n': ':star2:',  # clear sky (night)
        '02d': ':sun_small_cloud:',  # few clouds (day)
        '02n': ':stars:',  # few clouds (night)
        '03d': ':mostly_sunny:',  # scattered clouds (day)
        '03n': ':mostly_sunny:',  # scattered clouds (night)
        '04d': ':sun_behind_cloud:',  # broken clouds (day)
        '04n': ':sun_behind_cloud:',  # broken clouds (night)
        '09d': ':rain_cloud:',  # shower rain (day)
        '09n': ':rain_cloud:',  # shower rain (night)
        '10d': ':partly_sunny_rain:',  # rain (day)
        '10n': ':sun_behind_rain_cloud:',  # rain (night)
        '11d': ':lightning_cloud:',  # thunderstorm (day)
        '11n': ':lightning_cloud:',  # thunderstorm (night)
        '13d': ':snow_cloud:',  # snow (day)
        '13n': ':snow_cloud:',  # snow (night)
        '50d': ':fog:',  # mist/fog (day)
        '50n': ':fog:',  # mist/fog (night)
    }
    return emoji_map.get(weather_icon, ':cloud:')  # default to cloud


def display_weather_data(df, city):
    if not df.empty:
        st.subheader(f"Weather Data for {city}")
        hours = (pd.to_datetime(df['dt_iso'].str.replace(' +0000 UTC', '', regex=True)).max() -
                 pd.to_datetime(df['dt_iso'].str.replace(' +0000 UTC', '', regex=True)).min()).total_seconds() / 3600
        st.write(f"Timespan: {hours:.1f} hours")

        for _, row in df.iterrows():
            emoji = get_weather_emoji(row['weather_icon'])
            icon_url = f"http://openweathermap.org/img/wn/{row['weather_icon']}@2x.png"
            cols = st.columns([1, 1, 3])
            with cols[0]:
                st.image(icon_url, width=50)
            with cols[1]:
                st.markdown(emoji)
            with cols[2]:
                timestamp = row['dt_iso'].replace(' +0000 UTC', '')
                st.write(f"**{timestamp}**")
                st.write(f"{row['weather_description'].capitalize()}")
                st.write(f"Temp: {row['temp']:.1f}°C, Humidity: {row['humidity']}%, Wind: {row['wind_speed']:.1f} m/s")
    else:
        st.warning("No weather data available. Check time range or CSV data.")


def plot_weather_data(df, city):
    if not df.empty:
        df['dt_iso_clean'] = pd.to_datetime(df['dt_iso'].str.replace(' +0000 UTC', '', regex=True),
                                            format='%Y-%m-%d %H:%M:%S', errors='coerce')
        fig_temp = px.line(df, x='dt_iso_clean', y='temp',
                           title=f'Temperature in {city} (°C)',
                           labels={'dt_iso_clean': 'Time', 'temp': 'Temperature (°C)'})
        fig_humidity = px.line(df, x='dt_iso_clean', y='humidity',
                               title=f'Humidity in {city} (%)',
                               labels={'dt_iso_clean': 'Time', 'humidity': 'Humidity (%)'})
        fig_wind = px.line(df, x='dt_iso_clean', y='wind_speed',
                           title=f'Wind Speed in {city} (m/s)',
                           labels={'dt_iso_clean': 'Time', 'wind_speed': 'Wind Speed (m/s)'})
        st.plotly_chart(fig_temp, use_container_width=True)
        st.plotly_chart(fig_humidity, use_container_width=True)
        st.plotly_chart(fig_wind, use_container_width=True)


def st_init_page():
    st.set_page_config(
        page_title="Datenvisualisierung",
        page_icon=":twisted_rightwards_arrows:",
        layout="wide"
    )


def st_init_sst():
    if 'points' not in st.session_state:
        st.session_state.points = [{"coords": [random.uniform(-0.01, 0.01) + 46.9480,
                                               random.uniform(-0.01, 0.01) + 7.4474],
                                    "color": f'rgba(49, 134, 204, 1)'}]
    if 'city' not in st.session_state:
        st.session_state.city = "Bern"
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = pd.DataFrame()
    if 'start_datetime' not in st.session_state:
        st.session_state.start_datetime = datetime(2023, 1, 1, 0, 0)
    if 'end_datetime' not in st.session_state:
        st.session_state.end_datetime = datetime(2023, 1, 1, 23, 0)
    if 'show_data' not in st.session_state:
        st.session_state.show_data = False


def main():
    st_init_page()
    st_init_sst()

    # File upload as fallback
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

    cities = {
        "Bern": [46.9480, 7.4474],
        "Zurich": [47.3769, 8.5417]
    }

    # Initialize default filtered data
    if st.session_state.filtered_df.empty and wetter_Bern is not None:
        st.session_state.filtered_df = filter_weather_data(wetter_Bern,
                                                           st.session_state.start_datetime,
                                                           st.session_state.end_datetime)
        if not st.session_state.filtered_df.empty:
            st.session_state.city = "Bern"

    left, middle, right = st.columns([1, 3, 1])

    with left:
        st.header("Controls")
        page = st.selectbox("Page", ["map", "moves"])
        st.session_state.city = st.selectbox("City", ["Bern", "Zurich", "both"])
        start_date = st.date_input("Start date", value=datetime(2023, 1, 1))
        start_time = st.time_input("Start time", value=datetime(2023, 1, 1, 0, 0).time())
        end_date = st.date_input("End date", value=datetime(2023, 1, 1))
        end_time = st.time_input("End time", value=datetime(2023, 1, 1, 23, 0).time())

        # Combine date and time for preview
        temp_start_datetime = datetime.combine(start_date, start_time)
        temp_end_datetime = datetime.combine(end_date, end_time)

        if st.button("Action"):
            st.session_state.start_datetime = temp_start_datetime
            st.session_state.end_datetime = temp_end_datetime
            wetter = None
            if st.session_state.city == "Bern" and wetter_Bern is not None:
                wetter = wetter_Bern
            elif st.session_state.city == "Zurich" and wetter_Zurich is not None:
                wetter = wetter_Zurich
            elif st.session_state.city == "both" and wetter_Bern is not None and wetter_Zurich is not None:
                wetter = pd.concat([wetter_Bern, wetter_Zurich])
            if wetter is None:
                st.error(f"No data available for {st.session_state.city}. Check CSV files.")
                st.session_state.filtered_df = pd.DataFrame()
            else:
                st.session_state.filtered_df = filter_weather_data(wetter,
                                                                   st.session_state.start_datetime,
                                                                   st.session_state.end_datetime)
            city_coords = cities.get(st.session_state.city, cities["Bern"])
            if st.session_state.city == "both":
                city_coords = [(cities["Bern"][0] + cities["Zurich"][0]) / 2,
                               (cities["Bern"][1] + cities["Zurich"][1]) / 2]
            st.session_state.points = [{"coords": [random.uniform(-0.01, 0.01) + city_coords[0],
                                                   random.uniform(-0.01, 0.01) + city_coords[1]],
                                        "color": f'rgba(49, 134, 204, 1)'}]
            st.session_state.show_data = False

        if st.button("View data"):
            st.session_state.show_data = True

        if st.button("Reload"):
            st_init_sst()
            if wetter_Bern is not None:
                st.session_state.filtered_df = filter_weather_data(wetter_Bern,
                                                                   datetime(2023, 1, 1, 0, 0),
                                                                   datetime(2023, 1, 1, 23, 0))
                st.session_state.city = "Bern"
            st.rerun()

    with middle:
        if page == "map":
            st.header("Visualizations")
            if not st.session_state.filtered_df.empty:
                representative_df = get_representative_weather(st.session_state.filtered_df,
                                                               st.session_state.start_datetime,
                                                               st.session_state.end_datetime)
                # Display map
                if st.session_state.city == "both":
                    center = [(cities["Bern"][0] + cities["Zurich"][0]) / 2,
                              (cities["Bern"][1] + cities["Zurich"][1]) / 2]
                    m = display_map(center, st.session_state.points, zoom=9)
                    folium.Marker(cities["Bern"], popup="Bern").add_to(m)
                    folium.Marker(cities["Zurich"], popup="Zurich").add_to(m)
                    st.components.v1.html(m._repr_html_(), height=800)
                else:
                    m = display_map(cities[st.session_state.city], st.session_state.points)
                    st.components.v1.html(m._repr_html_(), height=800)

                # Display weather data and plots
                display_weather_data(representative_df, st.session_state.city)
                plot_weather_data(representative_df, st.session_state.city)

                # Display filtered DataFrame if View data is clicked
                if st.session_state.show_data:
                    st.subheader("Filtered Weather Data")
                    st.dataframe(st.session_state.filtered_df[
                                     ['dt_iso', 'temp', 'humidity', 'wind_speed', 'weather_description']],
                                 use_container_width=True)
            else:
                st.warning("No valid data loaded. Check time range or CSV data.")
        else:
            st.warning("Moves page not yet implemented.")

    with right:
        st.header("Instructions & Comments")
        st.markdown("""
        ### Instructions
        - **Upload (Sidebar)**: Upload Bern/Zurich CSV files if not in `arbeit/wetter/`.
        - **Controls (Left)**: 
          - Select a page ('map' or 'moves').
          - Choose a city ('Bern', 'Zurich', or 'both').
          - Set start/end date and time (defaults to Jan 1, 2023).
          - Click **Action** to apply filters and update visualizations.
          - Click **View data** to see filtered data in a table in the middle column.
          - Click **Reload** to reset to Bern, Jan 1, 2023.
        - **Visualizations (Middle)**:
          - Shows a map with a random point for the selected city/time.
          - Displays weather data (emoji, icon, temp, humidity, wind) for ~10 representative points.
          - Includes plots for temperature, humidity, and wind speed.
          - Shows filtered data table when 'View data' is clicked.
        - **Notes**:
          - For timespans >10 hours, every other hour is shown.
          - For multiple days, daily averages and most frequent weather are displayed.
          - 'both' city option shows combined data and a map centered between Bern/Zurich.
          - CSV files must have 8760 rows (hourly 2023 data) with dt_iso as 'YYYY-MM-DD HH:MM:SS +0000 UTC'.
          - Weather emojis and icons require internet access.
          - 'moves' page is not implemented.
        """)


if __name__ == "__main__":
    main()