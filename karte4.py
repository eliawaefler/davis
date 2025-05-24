import folium
import streamlit as st
import random

def create_abstract_map():
    # City centers
    cities = {
        "Bern": [46.9480, 7.4474],
        "Zurich": [47.3769, 8.5417]
    }

    # Initial random points
    if "points" not in st.session_state:
        st.session_state.points = [[random.uniform(-0.01, 0.01) + cities["Bern"][0],
                                    random.uniform(-0.01, 0.01) + cities["Bern"][1]] for _ in range(3)]

    # City selection
    city = st.selectbox("", ["Bern", "Zurich"])

    # Button to move points
    if st.button(""):
        st.session_state.points = [[random.uniform(-0.01, 0.01) + cities[city][0],
                                    random.uniform(-0.01, 0.01) + cities[city][1]] for _ in range(3)]

    # Create abstract map
    m = folium.Map(
        location=cities[city],
        zoom_start=13,
        tiles="cartodbpositron",
        attr="",
        zoom_control=False,
        scrollWheelZoom=False,
        dragging=False
    )

    # Add points
    for point in st.session_state.points:
        folium.CircleMarker(
            location=point,
            radius=5,
            color="#3186cc",
            fill=True,
            fill_color="#3186cc"
        ).add_to(m)

    # Display map
    st.components.v1.html(m._repr_html_(), height=500)

if __name__ == "__main__":
    create_abstract_map()