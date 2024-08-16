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

# Initialize session state variables
if "marker" not in st.session_state:
    st.session_state["marker"] = [28.6139, 77.2090]  # Delhi coordinates
if "api_result" not in st.session_state:
    st.session_state["api_result"] = None
if "rainfall_data" not in st.session_state:
    st.session_state["rainfall_data"] = [
        2.7715942327085665,
        0.7863158647851064,
        0.12182573777622914,
        0.06965268364875025,
        0.7598821146230067,
        2.4584453831794897,
        6.331687329766313,
        2.96728587006872,
        4.837692532803455,
        5.647026369003688,
        0.14140295145352866,
        0.003789064855178973,
    ]
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [28.6139, 77.2090]  # Delhi
if "iframe_center" not in st.session_state:
    st.session_state["iframe_center"] = [40.1028, -74.4060]  # New York for iframe


st.set_page_config(layout="wide")  # Use wide layout to maximize space
# Define months
months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

PRIMARY_COLOR = "#430f8e"
SECONDARY_COLOR = "#950f3b"
TERTIARY_COLOR = "#9f0d30"
QUATERNARY_COLOR = "#620f6f"
BG_COLOR = "#2E0A3A"
TEXT_COLOR = "#E6D9F2"


# Function to reset map and data
def reset_map_and_data():
    st.session_state["marker"] = None
    st.session_state["api_result"] = None
    st.session_state["rainfall_data"] = [0] * 12
    st.session_state["map_center"] = [40.1028, -74.4060]  # Reset to default


# Function to make API call
def make_api_call(lat, lon):
    url = f"https://www.fused.io/server/v1/realtime-shared/fsh_3w7IJbltI8eSVQMXZmUptj/run/file"
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


# Function to parse rainfall data
def parse_rainfall_data(api_result):
    csv_data = io.StringIO(api_result.decode("utf-8"))
    df = pd.read_csv(csv_data)
    rainfall_data = eval(df["rainfall"].iloc[0])
    return pd.DataFrame({"Month": months, "Rainfall": rainfall_data})


def generate_html_content(rainfall_data, center_lat, center_lon):
    rainfall_array_json = json.dumps(rainfall_data)
    rainfall_array_encoded = urllib.parse.quote(rainfall_array_json)

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
            #stopwatch {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(255, 255, 255, 0.8);
                padding: 5px 10px;
                border-radius: 3px;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="legend"></div>
        <div id="stopwatch">Loading time: 0.00s</div>
        <script>
            let startTime;
            let stopwatchInterval;
            let isTimerRunning = false;
            let tilesLoading = 0;
            let completionTimeout;

            function startStopwatch() {{
                if (!isTimerRunning) {{
                    console.log('Starting stopwatch');
                    startTime = Date.now();
                    stopwatchInterval = setInterval(updateStopwatch, 10);
                    isTimerRunning = true;
                    document.getElementById('stopwatch').textContent = 'Loading time: 0.00s';
                }}
            }}

            function stopStopwatch() {{
                if (isTimerRunning) {{
                    console.log('Stopping stopwatch');
                    clearInterval(stopwatchInterval);
                    isTimerRunning = false;
                    const finalTime = ((Date.now() - startTime) / 1000).toFixed(2);
                    document.getElementById('stopwatch').textContent = `Loading time: ${{finalTime}}s (Completed)`;
                }}
            }}

            function updateStopwatch() {{
                const elapsedTime = (Date.now() - startTime) / 1000;
                document.getElementById('stopwatch').textContent = `Loading time: ${{elapsedTime.toFixed(2)}}s`;
            }}

            function resetAndStartStopwatch() {{
                console.log('Resetting and starting stopwatch');
                clearTimeout(completionTimeout);
                if (isTimerRunning) {{
                    clearInterval(stopwatchInterval);
                    isTimerRunning = false;
                }}
                tilesLoading = 0;
                startStopwatch();
            }}

            function scheduleStopwatch() {{
                console.log('Scheduling stopwatch stop');
                clearTimeout(completionTimeout);
                completionTimeout = setTimeout(() => {{
                    console.log('Completion timeout triggered');
                    stopStopwatch();
                }}, 1000);
            }}

            mapboxgl.accessToken = 'pk.eyJ1IjoibWlsaW5kc29uaSIsImEiOiJjbDRjc2ZxaTgwMW5hM3Bqbmlka3VweWVkIn0.AM0QzfbGzUZc04vZ6o2uaw';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/dark-v10',
                zoom: 7,
                center: [{center_lon}, {center_lat}]
            }});

            const popup = new mapboxgl.Popup({{
                closeButton: false,
                closeOnClick: false
            }});

            const colorScale = chroma.scale(['blue','yellow', 'red']);
            
            map.on('load', () => {{
                console.log('Map loaded');
                map.addSource('fused-vector-source', {{
                    'type': 'vector',
                    'tiles': [
                        'https://www.fused.io/server/v1/realtime-shared/fsh_LfRybzrLngj3vZEHvBRDe/run/tiles/{{z}}/{{x}}/{{y}}?dtype_out_vector=mvt&input_array={rainfall_array_encoded}'
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
                            ['get', 'similarity'],
                            0, colorScale(0).hex(),
                            1, colorScale(1).hex()
                        ],
                        'fill-opacity': 0.7
                    }}
                }});

                resetAndStartStopwatch();

                map.on('sourcedata', (e) => {{
                    if (e.isSourceLoaded && e.sourceId === 'fused-vector-source') {{
                        console.log('Source data loaded');
                        tilesLoading = Math.max(0, tilesLoading - 1);
                        console.log('Tiles still loading:', tilesLoading);
                        if (tilesLoading === 0) {{
                            scheduleStopwatch();
                        }}
                    }}
                }});

                map.on('dataloading', (e) => {{
                    if (e.sourceId === 'fused-vector-source') {{
                        console.log('Data loading started');
                        tilesLoading++;
                        console.log('Tiles loading:', tilesLoading);
                        resetAndStartStopwatch();
                    }}
                }});

                map.on('idle', () => {{
                    console.log('Map idle');
                    if (tilesLoading === 0 && isTimerRunning) {{
                        scheduleStopwatch();
                    }}
                }});

                map.on('movestart', () => {{
                    console.log('Map move started');
                    resetAndStartStopwatch();
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
                const gradientSteps = 5;
                for (let i = 0; i <= gradientSteps; i++) {{
                    const step = i / gradientSteps;
                    const color = colorScale(step).hex();
                    legend.innerHTML += `<div style="background: ${{color}}; width: 20px; height: 20px; display: inline-block;"></div>`;
                }}
                legend.innerHTML += '<br>Low Similarity <span style="float: right;">High Similarity</span>';
            }});

 
        
             map.on('error', (e) => {{
                console.error('Mapbox GL JS error:', e);
                stopStopwatch();
                document.getElementById('stopwatch').textContent += ' (Error)';
            }});
        </script>
    </body>
    </html>
    """
    return html_content


@st.dialog("Edit Rainfall Data")
def edit_rainfall_data():
    st.write("Edit the rainfall data below. Changes will update the map and plot.")

    rainfall_df = pd.DataFrame(
        {"Month": months, "Rainfall": st.session_state["rainfall_data"]}
    )

    edited_df = st.data_editor(
        rainfall_df,
        num_rows="fixed",
        key="modal_rainfall_editor",
        use_container_width=True,
    )

    if st.button("Apply Changes"):
        st.session_state["rainfall_data"] = edited_df["Rainfall"].tolist()
        st.rerun()

    if st.button("Reset Rainfall Data"):
        st.session_state["rainfall_data"] = [0] * 12  # Reset to initial values
        st.rerun()


# Main app
st.title("Twin City App")

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

        # Add the default marker for Delhi
        folium.Marker(st.session_state["marker"]).add_to(m)

        output = st_folium(m, width=None, height=400, returned_objects=["last_clicked"])

        if output["last_clicked"]:
            clicked_lat = output["last_clicked"]["lat"]
            clicked_lon = output["last_clicked"]["lng"]

            if st.session_state["marker"] != [clicked_lat, clicked_lon]:
                st.session_state["marker"] = [clicked_lat, clicked_lon]
                st.session_state["map_center"] = [clicked_lat, clicked_lon]

                api_result = make_api_call(clicked_lat, clicked_lon)
                st.session_state["api_result"] = api_result

                rainfall_df = parse_rainfall_data(api_result)
                st.session_state["rainfall_data"] = rainfall_df["Rainfall"].tolist()

                st.rerun()

    with col2:
        st.subheader("Parameter Selection 📊")
        parameter = st.selectbox("Select Parameter", ["Precipitation"])

        # Display enhanced rainfall plot with custom color scheme
        plot_df = pd.DataFrame(
            {"Month": months, "Rainfall": st.session_state["rainfall_data"]}
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=plot_df["Month"],
                y=plot_df["Rainfall"],
                marker_color=plot_df["Rainfall"],
                marker_colorscale=[
                    PRIMARY_COLOR,
                    QUATERNARY_COLOR,
                    SECONDARY_COLOR,
                    TERTIARY_COLOR,
                ],
            )
        )

        fig.update_layout(
            title="Monthly Rainfall for Selected Location",
            xaxis_title="Month",
            yaxis_title="Rainfall (mm)",
            font=dict(color=TEXT_COLOR),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=350,
        )

        fig.update_xaxes(showgrid=False, tickfont=dict(color=TEXT_COLOR))
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(230,217,242,0.1)",
            tickfont=dict(color=TEXT_COLOR),
        )

        st.plotly_chart(fig, use_container_width=True)

# Full-width container for the iframe map
st.subheader("Hex-Similarity Map")
html_content = generate_html_content(
    st.session_state["rainfall_data"],
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
st.button("Edit Rainfall Data", on_click=edit_rainfall_data)
 
