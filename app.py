import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Cohort Map", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("map.csv")

    if "Unnamed: 5" in df.columns:
        df = df.drop(columns=["Unnamed: 5"])

    df.columns = [col.strip() for col in df.columns]

    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["Spots left"] = pd.to_numeric(df["Spots left"], errors="coerce")
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    df = df.dropna(subset=["Latitude", "Longitude"])

    return df

df = load_data()

st.title("Cohort Map")

col1, col2, col3 = st.columns(3)
col1.metric("Total Cities", len(df))
col2.metric("Cohorts", df["Group"].nunique())

st.markdown("---")

if not df.empty:
    map_df = df.copy()
    map_df["Start Date Display"] = map_df["Start Date"].dt.strftime("%Y-%m-%d")

    unique_groups = sorted(map_df["Group"].dropna().unique())
    color_palette = [
        [255, 99, 132, 180],
        [54, 162, 235, 180],
        [255, 206, 86, 180],
        [75, 192, 192, 180],
        [153, 102, 255, 180],
        [255, 159, 64, 180],
        [46, 204, 113, 180],
        [231, 76, 60, 180],
        [52, 73, 94, 180],
        [241, 196, 15, 180],
    ]

    group_color_map = {
        group: color_palette[i % len(color_palette)]
        for i, group in enumerate(unique_groups)
    }

    map_df["color"] = map_df["Group"].map(group_color_map)
    map_df["radius"] = 12000

    view_state = pdk.ViewState(
        latitude=map_df["Latitude"].mean(),
        longitude=map_df["Longitude"].mean(),
        zoom=4,
        pitch=0,
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[Longitude, Latitude]",
        get_radius=6,                 # constant size
        radius_units="pixels",        # size stays screen-based
        radius_min_pixels=3,
        radius_max_pixels=8,
        get_fill_color="color",
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1,
        pickable=True,
    )

    tooltip = {
        "html": """
        <b>Name:</b> {Name} <br/>
        <b>Group:</b> {Group} <br/>
        <b>Start Date:</b> {Start Date Display} <br/>
        <b>Location:</b> {Location} <br/>
        <b>Spots Left:</b> {Spots left}
        """,
        "style": {
            "backgroundColor": "white",
            "color": "black"
        }
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_provider="carto",
            map_style="light",
        )
    )

    st.subheader("Group Legend")
    legend_html = ""
    for group in unique_groups:
        color = group_color_map[group]
        legend_html += f"""
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <div style="
                width:16px;
                height:16px;
                background-color: rgba({color[0]}, {color[1]}, {color[2]}, 1);
                border-radius:50%;
                margin-right:8px;
            "></div>
            <div>{group}</div>
        </div>
        """

    st.markdown(legend_html, unsafe_allow_html=True)

else:
    st.warning("No valid coordinates found in the dataset.")