import pandas
import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta
import numpy as np
import folium
import random
from pyproj import Transformer
import plotly.express as px


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


def get_representative_weather(df, duration, unit):
    if df.empty:
        return df
    if unit == "Months":
        df['date'] = pd.to_datetime(df['dt'], unit='s').dt.date
        daily = df.groupby('date').agg({
            'temp': 'mean',
            'humidity': 'mean',
            'wind_speed': 'mean',
            'weather_icon': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
            'weather_description': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
            'dt': 'first'
        }).reset_index()
        if len(daily) > duration:
            indices = np.linspace(0, len(daily) - 1, duration, dtype=int)
            daily = daily.iloc[indices]
        return daily
    elif unit == "Days":
        df['date'] = pd.to_datetime(df['dt'], unit='s').dt.date
        daily = df.groupby('date').agg({
            'temp': 'mean',
            'humidity': 'mean',
            'wind_speed': 'mean',
            'weather_icon': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
            'weather_description': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0],
            'dt': 'first'
        }).reset_index()
        if len(daily) > duration:
            indices = np.linspace(0, len(daily) - 1, duration, dtype=int)
            daily = daily.iloc[indices]
        return daily
    else:  # Hours
        if len(df) > duration:
            indices = np.linspace(0, len(df) - 1, duration, dtype=int)
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


def temp_to_color(temp):
    if temp < 0:
        return f"background-color: #ADD8E6"  # Light blue for subzero
    elif temp < 10:
        return f"background-color: #90EE90"  # Light green
    elif temp < 20:
        return f"background-color: #FFFFE0"  # Light yellow
    else:
        return f"background-color: #FF6347"  # Tomato red


def rain_bar(rain):
    if rain >= 0.01:
        max_rain = 1.5  # Max rain for scaling
        width = min(rain / max_rain * 100, 100)  # Scale bar width
        return f"""
        <div style='width: {width}%; background-color: #1E90FF; height: 10px; border-radius: 5px;'></div>
        """
    else:
        return f"""
        <div style='width: {0}%; background-color: #1E90FF; height: 10px; border-radius: 5px;'></div>
        """


def wind_visual(wind_speed):
    max_wind = 20  # Max wind speed for scaling
    width = min(wind_speed / max_wind * 100, 100)
    return f"""
    <div style='width: {width}%; background-color: #B0C4DE; height: 10px; border-radius: 5px;'></div>
    {'💨' * int(wind_speed // 5)}  <!-- Emoji intensity -->
    """


def load_mobility_data(file_path):
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if df.empty:
                st.error(f"No data in {file_path}.")
                return None
            return df
        else:
            st.error(f"File {file_path} does not exist.")
            return None
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None


def main():
    st.set_page_config(page_title="Weather Visualization", layout="wide")

    # Initialize session state for points
    if 'points' not in st.session_state:
        st.session_state.points = []

    # Load weather data
    default_path_bern = "arbeit/wetter/bern_23_clean.csv"
    default_path_zurich = "arbeit/wetter/zurich_23_clean.csv"
    wetter_Bern = load_weather_data(default_path_bern, default_path_bern)
    wetter_Zurich = load_weather_data(default_path_zurich, default_path_zurich)

    # Load mobility data
    #default_mobility_path = "arbeit/mobility/mobility_data.csv"
    default_mobility_path = "arbeit/mobility_zurich/standorte.csv"
    zurich_points_df = pandas.read_csv(default_mobility_path)


    show_weather_rain = False
    show_weather_temp = False
    show_weather_wind = False

    cities = {
        "Bern": [46.9480, 7.4474],
        "Zurich": [47.3769, 8.5417]
    }
    left, b, middle, c, right = st.columns([2, 1, 10, 1, 2])

    with left:
        st.header("Controls")
        city = st.selectbox("City", ["Bern", "Zurich", "both"], index=1)
        start_date = st.date_input("Start date", value=datetime(2023, 1, 1))
        start_datetime = datetime(start_date.year, start_date.month, start_date.day, 1)  # Set to 01:00 UTC
        start_timestamp = int(start_datetime.timestamp())
        st.write(f"Timestamp: {start_timestamp}")
        unit = st.selectbox("Unit", ["Hours", "Days", "Months"])
        duration = st.slider("Duration", 1, 24 if unit == "Hours" else 31, 12 if unit == "Hours" else 10)

        show_dataf = st.toggle("show data")
        show_weather = st.toggle("show weather average")
        if st.toggle("show weather detail", True):
            show_weather_rain = st.toggle("show rain")
            show_weather_temp = st.toggle("show temp")
            show_weather_wind = st.toggle("show wind")

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
            # Update points based on zurich_points_df
            st.session_state.points = []
            if zurich_points_df is not None and city in ["Zurich", "both"]:
                for _, row in zurich_points_df.iterrows():
                    # Extract easting and northing from geometry
                    geom = row['geometry'].replace('POINT (', '').replace(')', '')
                    easting, northing = map(float, geom.split())
                    lat, lon = swiss_to_wgs84(easting, northing)
                    st.session_state.points.append({
                        "coords": [lat, lon],
                        "color": f'rgba(49, 134, 204, 1)'
                    })
            elif city == "Bern":
                # Fallback to a single point for Bern
                city_coords = cities.get(city, cities["Bern"])
                st.session_state.points = [{
                    "coords": [city_coords[0], city_coords[1]],
                    "color": f'rgba(49, 134, 204, 1)'
                }]

    with middle:
        st.header("wie beeinflusst das Wetter die Nutzung von Verkehrsmitteln in Bern und Zürich?")
        st.write("in dieser Datenvisualisierung kann für das Jahr 2023 Wetter und Mobilitätsdaten verglichen werden.")
        st.write("dieser Prototyp ist ein zwischenstand, es werden weitere Daten, Visualisierungen und (statistische) Auswertungen hinzugefügt.")
        if not filtered_df.empty:
            representative_df = get_representative_weather(filtered_df, duration, unit)
            if not representative_df.empty:
                st.subheader("Weather Conditions")
                cols = st.columns(len(representative_df))
                for i, (col, row) in enumerate(zip(cols, representative_df.iterrows())):
                    with col:
                        timestamp = pd.to_datetime(row[1]['dt'], unit='s')
                        if unit == "Hours":
                            label = timestamp.strftime('%H:%M')
                        elif unit == "Days":
                            label = timestamp.strftime('%d.%m.')
                        else:  # Months
                            label = timestamp.strftime('%b')
                        st.write(label)
                        if show_weather:
                            emoji = get_weather_emoji(row[1]['weather_icon'])
                            if st.button(f"{emoji}", key=f"{emoji}_{i}"):
                                st.write(
                                    f"{emoji} {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {row[1]['weather_description'].capitalize()} "
                                    f"(Temp: {row[1]['temp']:.1f}°C, Humidity: {row[1]['humidity']}%, Wind: {row[1]['wind_speed']:.1f} m/s)")
                        if show_weather_wind:
                            wind_speed = row[1]['wind_speed']
                            st.markdown(f"Wind: {wind_speed:.1f} m/s {wind_visual(wind_speed)}", unsafe_allow_html=True)

                        if show_weather_rain:
                            rain = row[1].get('rain_1h', 0)
                            if rain >= 0:
                                st.markdown(f"{rain} mm 🌧️ {rain_bar(rain)}", unsafe_allow_html=True)
                            else:
                                st.markdown(f"trocken {rain_bar(rain)}", unsafe_allow_html=True)

                        if show_weather_temp:
                            temp = row[1]['temp']
                            st.markdown(
                                f"<div style='{temp_to_color(temp)}; padding: 5px; border-radius: 5px;'>Temp: {temp:.1f}°C 🌡️</div>",
                                unsafe_allow_html=True
                            )

            if show_dataf:
                st.subheader("Data Table")
                st.dataframe(filtered_df[['dt', 'dt_iso', 'temp', 'humidity', 'wind_speed', 'weather_description']],
                             use_container_width=True)
                if zurich_points_df is not None:
                    st.dataframe(zurich_points_df, use_container_width=True)
        else:
            st.warning("No weather data available. Check time range or CSV data.")
        st.subheader("karte")
        if not filtered_df.empty:
            if city == "both":
                center = [(cities["Bern"][0] + cities["Zurich"][0]) / 2,
                          (cities["Bern"][1] + cities["Zurich"][1]) / 2]
                m = display_map(center, st.session_state.points, zoom=9)
                folium.Marker(cities["Bern"], popup="Bern").add_to(m)
                folium.Marker(cities["Zurich"], popup="Zurich").add_to(m)
            else:
                m = display_map(cities[city], st.session_state.points)
            st.components.v1.html(m._repr_html_(), height=600)
        else:
            st.warning("Map not displayed due to missing weather data.")

def old_main():
    st.set_page_config(page_title="Weather Visualization", layout="wide")

    # Initialize session state for points
    if 'points' not in st.session_state:
        st.session_state.points = [{"coords": [random.uniform(-0.01, 0.01) + 46.9480,
                                       random.uniform(-0.01, 0.01) + 7.4474],
                                    "color": f'rgba(49, 134, 204, 1)'}]

    # Load weather data
    default_path_bern = "arbeit/wetter/bern_23_clean.csv"
    default_path_zurich = "arbeit/wetter/zurich_23_clean.csv"
    wetter_Bern = load_weather_data(default_path_bern, default_path_bern)
    wetter_Zurich = load_weather_data(default_path_zurich, default_path_zurich)

    # Load mobility data
    default_mobility_path = "arbeit/mobility_zurich/standorte.csv"
    mobility_df = load_mobility_data(default_mobility_path)

    show_weather_rain = False
    show_weather_temp = False
    show_weather_wind = False

    cities = {
        "Bern": [46.9480, 7.4474],
        "Zurich": [47.3769, 8.5417]
    }
    left, b, middle, c, right = st.columns([2, 1, 10, 1, 2])

    with left:
        st.header("Controls")
        city = st.selectbox("City", ["Bern", "Zurich", "both"])
        start_date = st.date_input("Start date", value=datetime(2023, 1, 1))
        start_datetime = datetime(start_date.year, start_date.month, start_date.day, 1)  # Set to 01:00 UTC
        start_timestamp = int(start_datetime.timestamp())
        st.write(f"Timestamp: {start_timestamp}")
        unit = st.selectbox("Unit", ["Hours", "Days", "Months"])
        duration = st.slider("Duration", 1, 24 if unit == "Hours" else 31, 12 if unit == "Hours" else 10)

        show_dataf = st.toggle("show data")
        show_weather = st.toggle("show weather average")
        if st.toggle("show weather detail", True):
            show_weather_rain = st.toggle("show rain")
            show_weather_temp = st.toggle("show temp")
            show_weather_wind = st.toggle("show wind")

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
            # Update points based on selected city
            city_coords = cities.get(city, cities["Bern"])
            if city == "both":
                city_coords = [(cities["Bern"][0] + cities["Zurich"][0]) / 2,
                               (cities["Bern"][1] + cities["Zurich"][1]) / 2]
            st.session_state.points = [{"coords": [random.uniform(-0.01, 0.01) + city_coords[0],
                                                   random.uniform(-0.01, 0.01) + city_coords[1]],
                                        "color": f'rgba(49, 134, 204, 1)'}]

    with middle:
        st.header("wie beeinflusst das Wetter die Nutzung von Verkehrsmitteln in Bern und Zürich?")
        st.write("in dieser Datenvisualisierung kann für das Jahr 2023 Wetter und Mobilitätsdaten verglichen werden.")
        st.write("dieser Prototyp ist ein zwischenstand, es werden weitere Daten, Visualisierungen und (statistische) Auswertungen hinzugefügt.")
        if not filtered_df.empty:
            representative_df = get_representative_weather(filtered_df, duration, unit)
            if not representative_df.empty:
                st.subheader("Weather Conditions")
                cols = st.columns(len(representative_df))
                for i, (col, row) in enumerate(zip(cols, representative_df.iterrows())):
                    with col:
                        timestamp = pd.to_datetime(row[1]['dt'], unit='s')
                        if unit == "Hours":
                            label = timestamp.strftime('%H:%M')
                        elif unit == "Days":
                            label = timestamp.strftime('%d.%m.')
                        else:  # Months
                            label = timestamp.strftime('%b')
                        st.write(label)
                        if show_weather:
                            emoji = get_weather_emoji(row[1]['weather_icon'])
                            if st.button(f"{emoji}", key=f"{emoji}_{i}"):
                                st.write(
                                    f"{emoji} {timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {row[1]['weather_description'].capitalize()} "
                                    f"(Temp: {row[1]['temp']:.1f}°C, Humidity: {row[1]['humidity']}%, Wind: {row[1]['wind_speed']:.1f} m/s)")
                        if show_weather_wind:
                            wind_speed = row[1]['wind_speed']
                            st.markdown(f"Wind: {wind_speed:.1f} m/s {wind_visual(wind_speed)}", unsafe_allow_html=True)

                        if show_weather_rain:
                            rain = row[1].get('rain_1h', 0)
                            if rain >= 0:
                                st.markdown(f"{rain} mm 🌧️ {rain_bar(rain)}", unsafe_allow_html=True)
                            else:
                                st.markdown(f"trocken {rain_bar(rain)}", unsafe_allow_html=True)

                        if show_weather_temp:
                            temp = row[1]['temp']
                            st.markdown(
                                f"<div style='{temp_to_color(temp)}; padding: 5px; border-radius: 5px;'>Temp: {temp:.1f}°C 🌡️</div>",
                                unsafe_allow_html=True
                            )

            if show_dataf:
                st.subheader("Data Table")
                st.dataframe(filtered_df[['dt', 'dt_iso', 'temp', 'humidity', 'wind_speed', 'weather_description']],
                             use_container_width=True)
                if mobility_df is not None:
                    st.dataframe(mobility_df, use_container_width=True)
        else:
            st.warning("No weather data available. Check time range or CSV data.")
        st.subheader("karte")
        if not filtered_df.empty:
            if city == "both":
                center = [(cities["Bern"][0] + cities["Zurich"][0]) / 2,
                          (cities["Bern"][1] + cities["Zurich"][1]) / 2]
                m = display_map(center, st.session_state.points, zoom=9)
                folium.Marker(cities["Bern"], popup="Bern").add_to(m)
                folium.Marker(cities["Zurich"], popup="Zurich").add_to(m)
            else:
                m = display_map(cities[city], st.session_state.points)
            st.components.v1.html(m._repr_html_(), height=600)
        else:
            st.warning("Map not displayed due to missing weather data.")

if __name__ == "__main__":
    main()