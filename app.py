import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Location Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("map.csv")

    if "Unnamed: 5" in df.columns:
        df = df.drop(columns=["Unnamed: 5"])

    df.columns = [col.strip() for col in df.columns]
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    df["Spots left"] = pd.to_numeric(df["Spots left"], errors="coerce")

    return df

df = load_data()

st.title("Location Map Dashboard")
st.write("Interactive map of locations by cohort/group.")

st.sidebar.header("Filters")

group_options = sorted(df["Group"].dropna().unique())
selected_groups = st.sidebar.multiselect(
    "Select Group(s)",
    options=group_options,
    default=group_options
)

date_options = sorted(df["Start Date"].dropna().dt.date.unique())
selected_dates = st.sidebar.multiselect(
    "Select Start Date(s)",
    options=date_options,
    default=date_options
)

filtered_df = df.copy()

if selected_groups:
    filtered_df = filtered_df[filtered_df["Group"].isin(selected_groups)]

if selected_dates:
    filtered_df = filtered_df[filtered_df["Start Date"].dt.date.isin(selected_dates)]

col1, col2, col3 = st.columns(3)
col1.metric("Total Locations", len(filtered_df))
col2.metric("Groups", filtered_df["Group"].nunique())
col3.metric("Total Spots Left", int(filtered_df["Spots left"].sum()) if not filtered_df.empty else 0)

st.markdown("---")

if not filtered_df.empty:
    map_df = filtered_df.copy()
    map_df["Start Date Display"] = map_df["Start Date"].dt.strftime("%Y-%m-%d")

    # Assign a different color to each group/cohort
    unique_groups = sorted(map_df["Group"].dropna().unique())
    color_palette = [
        [255, 99, 132, 180],   # pink/red
        [54, 162, 235, 180],   # blue
        [255, 206, 86, 180],   # yellow
        [75, 192, 192, 180],   # teal
        [153, 102, 255, 180],  # purple
        [255, 159, 64, 180],   # orange
        [46, 204, 113, 180],   # green
        [231, 76, 60, 180],    # red
        [52, 73, 94, 180],     # dark blue/gray
        [241, 196, 15, 180],   # gold
    ]

    group_color_map = {
        group: color_palette[i % len(color_palette)]
        for i, group in enumerate(unique_groups)
    }

    map_df["color"] = map_df["Group"].map(group_color_map)

    # Constant size for all points
    map_df["radius"] = 12000

    view_state = pdk.ViewState(
        latitude=map_df["Latitude"].mean(),
        longitude=map_df["Longitude"].mean(),
        zoom=4,
        pitch=0
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[Longitude, Latitude]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True
    )

    tooltip = {
        "html": """
        <b>Name:</b> {Name} <br/>
        <b>Address:</b> {Address} <br/>
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

    st.subheader("Map")
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip
        )
    )

    st.subheader("Group Color Legend")
    legend_cols = st.columns(min(len(unique_groups), 5))
    for i, group in enumerate(unique_groups):
        col = legend_cols[i % len(legend_cols)]
        color = group_color_map[group]
        col.markdown(
            f"""
            <div style="display:flex; align-items:center; margin-bottom:8px;">
                <div style="
                    width:16px;
                    height:16px;
                    background-color: rgba({color[0]}, {color[1]}, {color[2]}, 1);
                    border-radius:50%;
                    margin-right:8px;
                "></div>
                <div>{group}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.warning("No data matches the selected filters.")

st.subheader("Filtered Data")

display_df = filtered_df.copy()
if "Start Date" in display_df.columns:
    display_df["Start Date"] = display_df["Start Date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    display_df[
        ["Name", "Address", "Group", "Start Date", "Location", "Spots left", "Latitude", "Longitude"]
    ],
    use_container_width=True
)

csv = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_locations.csv",
    mime="text/csv"
)