

import folium
import streamlit as st
import random
import time
import numpy as np

def display_map(city, points):
    m = folium.Map(
        location=city,
        zoom_start=13,
        tiles="cartodbpositron",
        attr="",
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False
    )

    for point in points:
        # Ensure point is a dict with coords and color
        if isinstance(point, dict) and "coords" in point and "color" in point:
            folium.CircleMarker(
                location=point["coords"],
                radius=5,
                color=point["color"],
                fill=True,
                fill_color=point["color"]
            ).add_to(m)

    st.components.v1.html(m._repr_html_(), height=800)

def main():
    st.set_page_config(
        page_title="Datenvisualisierung Elia Wäfler",
        page_icon=":twisted_rightwards_arrows:",
        layout="wide"
    )

    cities = {
        "Bern": [46.9480, 7.4474],
        "Zurich": [47.3769, 8.5417]
    }

    # Initialize session state
    if "points" not in st.session_state:
        st.session_state.points = [
            {"coords": [random.uniform(-0.01, 0.01) + 46.9480, random.uniform(-0.01, 0.01) + 7.4474], "color": "#3186cc"}
            for _ in range(3)
        ]
    if "goals" not in st.session_state:
        st.session_state.goals = None
    if "interpolated" not in st.session_state:
        st.session_state.interpolated = []
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()

    left, middle, right = st.columns([1, 3, 1])
    with left:
        city = st.selectbox("", ["Bern", "Zurich"])
        if st.button(""):
            st.session_state.goals = [
                [random.uniform(-0.01, 0.01) + cities[city][0], random.uniform(-0.01, 0.01) + cities[city][1]]
                for _ in range(3)
            ]
            st.session_state.interpolated = []
            for i, point in enumerate(st.session_state.points):
                interp_coords = [
                    [
                        point["coords"][0] + j/10 * (st.session_state.goals[i][0] - point["coords"][0]),
                        point["coords"][1] + j/10 * (st.session_state.goals[i][1] - point["coords"][1])
                    ]
                    for j in range(1, 11)
                ]
                st.session_state.interpolated.append(interp_coords)
            st.session_state.step = 0
            st.session_state.last_update = time.time()

    with middle:
        while True:
            st.rerun()

            current_time = time.time()
            if current_time - st.session_state.last_update >= 0.1:  # 10 times per second
                display_points = []
                if st.session_state.goals and st.session_state.step < 10 and st.session_state.interpolated:
                    for i, point in enumerate(st.session_state.points):
                        # Current point
                        if st.session_state.step < len(st.session_state.interpolated[i]):
                            display_points.append({
                                "coords": st.session_state.interpolated[i][st.session_state.step],
                                "color": "#3186cc"
                            })
                        # Trail points
                        for j in range(st.session_state.step):
                            if j < len(st.session_state.interpolated[i]):
                                alpha = (1.0 - (st.session_state.step - j)/10) * 0.5
                                display_points.append({
                                    "coords": st.session_state.interpolated[i][j],
                                    "color": f'rgba(49, 134, 204, {alpha})'
                                })
                    st.session_state.step += 1
                    if st.session_state.step >= 10:
                        for i, point in enumerate(st.session_state.points):
                            point["coords"] = st.session_state.goals[i]
                        st.session_state.goals = None
                        st.session_state.interpolated = []
                        st.session_state.step = 0
                else:
                    display_points = st.session_state.points
                display_map(cities[city], display_points)
                st.session_state.last_update = current_time

if __name__ == "__main__":
    main()