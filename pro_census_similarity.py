import streamlit as st
import folium
from streamlit_folium import st_folium
import base64
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import json
import urllib.parse
from folium.plugins import MiniMap
import numpy as np

# Initialize session state variables
if "marker" not in st.session_state:
    st.session_state["marker"] = [40.7128, -74.0060]  # New York coordinates
if "api_result" not in st.session_state:
    st.session_state["api_result"] = None
if "census_data" not in st.session_state:
    st.session_state["census_data"] = [
        28.45501480941962,
        20.016028619991268,
        3.5507177524419262,
        5.676214709182359,
        5.9178629207365425,
        3.742785142036794,
        0,
        0,
        0,
        5.159073286643408,
        2.0500078501887287,
        3.5507177524419262,
        5.423810957329532,
        5.423810957329532,
        0,
        4.8799947800246,
        6.799106856359117,
        4.583956907430203,
        2.0500078501887287,
        2.899148904708212,
        4.100015700377457,
        7.1014355048838524,
        2.367145168294617,
        4.583956907430203,
        2.6465487544584723,
        20.224897183619504,
        1.1835725841473086,
        2.6465487544584723,
        3.3476488011081904,
        3.9254661737679664,
        2.6465487544584723,
        0,
        3.131438716247847,
        2.0500078501887287,
        4.734290336589234,
        3.131438716247847,
        3.5507177524419262,
        5.021473201662285,
        2.0500078501887287,
        5.2930975089169445,
        5.676214709182359,
        2.0500078501887287,
        2.367145168294617,
        5.159073286643408,
        7.199390966739485,
        5.798297809416424,
        4.267431640376538,
        7.485570284073588,
        4.734290336589234,
    ]
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [40.7128, -74.0060]  # New York
if "iframe_center" not in st.session_state:
    st.session_state["iframe_center"] = [
        47.068623358240856,
        -122.30586442765583,
    ]  # New York for iframe
# 44.00467058230901, -120.12475319498472 oregon
# 47.068623358240856, -122.30586442765583
census_labels = {
    "B01001_E001": "Total",
    "B01001_E002": "Male",
    "B01001_E003": "Male: Under 5",
    "B01001_E004": "Male: 5-9",
    "B01001_E005": "Male: 10-14",
    "B01001_E006": "Male: 15-17",
    "B01001_E007": "Male: 18-19",
    "B01001_E008": "Male: 20",
    "B01001_E009": "Male: 21",
    "B01001_E010": "Male: 22-24",
    "B01001_E011": "Male: 25-29",
    "B01001_E012": "Male: 30-34",
    "B01001_E013": "Male: 35-39",
    "B01001_E014": "Male: 40-44",
    "B01001_E015": "Male: 45-49",
    "B01001_E016": "Male: 50-54",
    "B01001_E017": "Male: 55-59",
    "B01001_E018": "Male: 60-61",
    "B01001_E019": "Male: 62-64",
    "B01001_E020": "Male: 65-66",
    "B01001_E021": "Male: 67-69",
    "B01001_E022": "Male: 70-74",
    "B01001_E023": "Male: 75-79",
    "B01001_E024": "Male: 80-84",
    "B01001_E025": "Male: 85+",
    "B01001_E026": "Female",
    "B01001_E027": "Female: Under 5",
    "B01001_E028": "Female: 5-9",
    "B01001_E029": "Female: 10-14",
    "B01001_E030": "Female: 15-17",
    "B01001_E031": "Female: 18-19",
    "B01001_E032": "Female: 20",
    "B01001_E033": "Female: 21",
    "B01001_E034": "Female: 22-24",
    "B01001_E035": "Female: 25-29",
    "B01001_E036": "Female: 30-34",
    "B01001_E037": "Female: 35-39",
    "B01001_E038": "Female: 40-44",
    "B01001_E039": "Female: 45-49",
    "B01001_E040": "Female: 50-54",
    "B01001_E041": "Female: 55-59",
    "B01001_E042": "Female: 60-61",
    "B01001_E043": "Female: 62-64",
    "B01001_E044": "Female: 65-66",
    "B01001_E045": "Female: 67-69",
    "B01001_E046": "Female: 70-74",
    "B01001_E047": "Female: 75-79",
    "B01001_E048": "Female: 80-84",
    "B01001_E049": "Female: 85+",
}


st.set_page_config(layout="wide")  # Use wide layout to maximize space

BAR_COLOR_SCALE = [
    [0, "#1a1a1a"],  # Dark grey
    [0.25, "#4d4d4d"],  # Medium dark grey
    [0.5, "#808080"],  # Medium grey
    [0.75, "#b3b3b3"],  # Light grey
    [1, "#e6e6e6"],  # Very light grey
]
TEXT_COLOR = "#b3b3b3"  # Dark grey text


# Function to reset map and data
def reset_map_and_data():
    st.session_state["marker"] = None
    st.session_state["api_result"] = None
    st.session_state["census_data"] = [0] * 49
    st.session_state["map_center"] = [40.7128, -74.0060]  # Reset to default


# Function to make API call
def make_api_call(lat, lon):
    url = f"https://www.fused.io/server/v1/realtime-shared/fsh_TqObjXaLDeV8WV5LvOrSK/run/file"
    params = {
        "dtype_out_raster": "png",
        "dtype_out_vector": "csv",
        "lat": lat,
        "lng": lon,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.content
    else:
        return f"Error: {response.status_code}"


# Function to parse census data
def parse_census_data(api_result):
    csv_data = io.StringIO(api_result.decode("utf-8"))
    df = pd.read_csv(csv_data)
    census_vector_str = df["census_vector"].iloc[0]
    # Remove square brackets and split the string
    census_vector_str = census_vector_str.strip("[]")
    census_vector = np.fromstring(census_vector_str, sep=" ")
    return census_vector.tolist()


def generate_html_content(census_data, center_lat, center_lon):
    census_array_json = json.dumps(census_data)
    census_array_encoded = urllib.parse.quote(census_array_json)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Vector Tile Map with Similarity-based Color Gradient and Tooltip</title>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.2.0/mapbox-gl.css" rel="stylesheet">
        <script src="https://api.mapbox.com/mapbox-gl-js/v3.2.0/mapbox-gl.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.4.2/chroma.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
            .mapboxgl-popup {{
                max-width: 400px;
                font: 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;
            }}
            #legend {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.8);
                padding: 10px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="legend"></div>
        <script>
            mapboxgl.accessToken = 'pk.eyJ1IjoibWlsaW5kc29uaSIsImEiOiJjbDRjc2ZxaTgwMW5hM3Bqbmlka3VweWVkIn0.AM0QzfbGzUZc04vZ6o2uaw';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/dark-v10',
                zoom: 8,
                center: [{center_lon}, {center_lat}]
            }});

            const popup = new mapboxgl.Popup({{
                closeButton: false,
                closeOnClick: false
            }});

            const colorScale = chroma.scale([
                '#FF0000',  // Red for lowest similarity
                '#FF7F00',  // Orange
                '#FFFF00',  // Yellow
                '#00FF00',  // Green
                '#0080FF',  // Light blue
                '#0000FF'   // Dark blue for highest similarity
            ]).mode('lch').domain([0, 0.2, 0.4, 0.6, 0.8, 1]);
            
            map.on('load', () => {{
                map.addSource('fused-vector-source', {{
                    'type': 'vector',
                    'tiles': [
                        `https://www.fused.io/server/v1/realtime-shared/fsh_3cKb0pcDk6LmBkHHSeEcn5/run/tiles/{{z}}/{{x}}/{{y}}?dtype_out_vector=mvt&census_vector={census_array_encoded}`
                    ],
                    'minzoom': 6,
                    'maxzoom': 14
                }});

                map.addLayer({{
                    'id': 'fused-vector-layer',
                    'type': 'fill',
                    'source': 'fused-vector-source',
                    'source-layer': 'udf',
                    'paint': {{
                        'fill-color': [
                            'interpolate',
                            ['linear'],
                            ['get', 'census_similarity'],
                            0, colorScale(0).hex(),
                            0.2, colorScale(0.2).hex(),
                            0.4, colorScale(0.4).hex(),
                            0.6, colorScale(0.6).hex(),
                            0.8, colorScale(0.8).hex(),
                            1, colorScale(1).hex()
                        ],
                        'fill-opacity': 0.7
                    }}
                }});

                map.on('mousemove', 'fused-vector-layer', (e) => {{
                    if (e.features.length > 0) {{
                        const feature = e.features[0];
                        const coordinates = e.lngLat;

                        let popupContent = '<h3>Feature Properties:</h3>';
                        for (const property in feature.properties) {{
                            popupContent += `<strong>${{property}}:</strong> ${{feature.properties[property]}}<br>`;
                        }}

                        popup.setLngLat(coordinates).setHTML(popupContent).addTo(map);
                    }}
                }});

                map.on('mouseleave', 'fused-vector-layer', () => {{
                    popup.remove();
                }});

                const legend = document.getElementById('legend');
                const gradientSteps = 6;
                for (let i = 0; i <= gradientSteps; i++) {{
                    const step = i / gradientSteps;
                    const color = colorScale(step).hex();
                    legend.innerHTML += `<div style="background: ${{color}}; width: 20px; height: 20px; display: inline-block;"></div>`;
                }}
                legend.innerHTML += '<br>Low Similarity <span style="float: right;">High Similarity</span>';
            }});

            map.on('error', (e) => {{
                console.error('Mapbox GL JS error:', e);
            }});
        </script>
    </body>
    </html>
    """
    return html_content


@st.dialog("Edit Census Data")
def edit_census_data():
    st.write("Edit the census data below. Changes will update the map and plot.")

    census_labels = [f"B01001_E{str(i).zfill(3)}" for i in range(1, 50)]
    census_df = pd.DataFrame(
        {"Label": census_labels, "Value": st.session_state["census_data"]}
    )

    edited_df = st.data_editor(
        census_df,
        num_rows="fixed",
        key="modal_census_editor",
        use_container_width=True,
    )

    if st.button("Apply Changes"):
        st.session_state["census_data"] = edited_df["Value"].tolist()
        st.rerun()

    if st.button("Reset Census Data"):
        st.session_state["census_data"] = [0] * 49  # Reset to initial values
        st.rerun()


# Main app
st.title("Census Data Dashboard")

# Create a container for the upper half of the page
upper_container = st.container()

with upper_container:
    col1, col2 = st.columns([3, 2])  # Adjust column ratio for better space utilization

with col1:
    st.subheader("Location Selector")
    m = folium.Map(
        location=st.session_state["map_center"],
        zoom_start=10,
        tiles=None,
    )

    minimap = MiniMap(
        tile_layer=folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains="abcd",
        ),
        zoom_level_offset=-8,
        width=150,
        height=150,
    )
    m.add_child(minimap)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="Dark Matter",
        control=False,
        subdomains="abcd",
    ).add_to(m)

    # Add the current marker
    folium.Marker(st.session_state["marker"]).add_to(m)

    output = st_folium(m, width=None, height=400, key="map")

    if output["last_clicked"] is not None:
        clicked_lat = output["last_clicked"]["lat"]
        clicked_lon = output["last_clicked"]["lng"]

        if st.session_state["marker"] != [clicked_lat, clicked_lon]:
            st.session_state["marker"] = [clicked_lat, clicked_lon]
            st.session_state["map_center"] = [clicked_lat, clicked_lon]
            st.session_state["iframe_center"] = [clicked_lat, clicked_lon]

            api_result = make_api_call(clicked_lat, clicked_lon)
            st.session_state["api_result"] = api_result

            if isinstance(api_result, bytes):  # Check if api_result is valid
                census_data = parse_census_data(api_result)
                st.session_state["census_data"] = census_data
            else:
                st.error(f"API call failed: {api_result}")

            st.rerun()

    # Display current marker location
    st.write(f"Current marker: {st.session_state['marker']}")

with col2:
    st.subheader("Census Data Visualization 📊")

    # Display enhanced census data plot with grey color scheme and new labels
    plot_df = pd.DataFrame(
        {
            "Label": [
                census_labels.get(
                    f"B01001_E{str(i).zfill(3)}", f"B01001_E{str(i).zfill(3)}"
                )
                for i in range(1, 50)
            ],
            "Value": st.session_state["census_data"],
        }
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=plot_df["Label"],
            y=plot_df["Value"],
            marker_color=plot_df["Value"],
            marker_colorscale=BAR_COLOR_SCALE,
        )
    )

    fig.update_layout(
        title="Population Distribution by Age and Sex",
        title_font_color=TEXT_COLOR,
        xaxis_title="Age Group",
        yaxis_title="Population Count",
        font=dict(color=TEXT_COLOR),
        plot_bgcolor="rgba(0,0,0,0)",  # Transparent plot background
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent paper background
        height=500,
        width=1200,
        margin=dict(l=50, r=50, t=50, b=100),
        xaxis=dict(
            rangeslider=dict(visible=True),
            tickangle=45,
            tickfont=dict(size=10),
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(color=TEXT_COLOR),
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(0,0,0,0.1)",  # Light grey grid
        tickfont=dict(color=TEXT_COLOR),
    )

    # Use st.plotly_chart with use_container_width=False to allow horizontal scrolling
    st.plotly_chart(fig, use_container_width=False)

    # Add custom CSS to make the chart container scrollable
    st.markdown(
        """
        <style>
        .stPlotlyChart {
            width: 100%;
            overflow-x: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Full-width container for the iframe map
st.subheader("Hex-Similarity Map")
html_content = generate_html_content(
    st.session_state["census_data"],
    st.session_state["iframe_center"][0],
    st.session_state["iframe_center"][1],
)
encoded_content = base64.b64encode(html_content.encode()).decode()
st.components.v1.iframe(
    f"data:text/html;base64,{encoded_content}",
    width=None,  # Use full width
    height=600,
    scrolling=True,
)

# Button to open the modal
st.button("Edit Census Data", on_click=edit_census_data)
