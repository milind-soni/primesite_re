import streamlit as st
import folium
from streamlit_folium import st_folium
import base64
import requests
import pandas as pd
import plotly.express as px
import io
import json
import urllib.parse

# Initialize session state for marker, API result, and map center
if "marker" not in st.session_state:
    st.session_state["marker"] = None
if "api_result" not in st.session_state:
    st.session_state["api_result"] = None
if "rainfall_data" not in st.session_state:
    st.session_state["rainfall_data"] = [0] * 12
if "map_center" not in st.session_state:
    st.session_state["map_center"] = [28.6171, 77.2168]  # Default to New York
if "iframe_center" not in st.session_state:
    st.session_state["iframe_center"] = [40.1028, -74.4060]  # New York for iframe


st.sidebar.title("Data Editor")

# Instructions
st.sidebar.write("Mark a location on the Location Selector map to get started!")

# Create editable dataframe in sidebar
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
rainfall_df = pd.DataFrame(
    {"Month": months, "Rainfall": st.session_state["rainfall_data"]}
)

edited_df = st.sidebar.data_editor(
    rainfall_df,
    num_rows="fixed",
    key="sidebar_rainfall_editor",
    use_container_width=True,
)

st.session_state["rainfall_data"] = edited_df["Rainfall"].tolist()

# Add a button to reset rainfall data
if st.sidebar.button("Reset Rainfall Data"):
    st.session_state["rainfall_data"] = [0] * 12  # Reset to initial values
    st.rerun()


def reset_map_and_data():
    st.session_state["marker"] = None
    st.session_state["api_result"] = None
    st.session_state["rainfall_data"] = [0] * 12
    st.session_state["map_center"] = [40.1028, -74.4060]  # Reset to default


def make_api_call(lat, lon):
    url = f"https://www.fused.io/server/v1/realtime-shared/fsh_3Ow5rXA7mNdewmdDEHgEQm/run/file"
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


def parse_rainfall_data(api_result):
    csv_data = io.StringIO(api_result.decode("utf-8"))
    df = pd.read_csv(csv_data)
    rainfall_data = eval(df["rainfall"].iloc[0])
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


st.title("Twin City App")

# Create two columns for side-by-side layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Location Selector")
    m = folium.Map(
        location=st.session_state["map_center"],
        zoom_start=10,
        tiles=None,  # We'll add our custom tile layer instead
        attr='Map tiles by <a href="https://carto.com">Carto</a>, under CC BY 3.0. Data by <a href="https://www.openstreetmap.org/">OpenStreetMap</a>, under ODbL.',
    )

    # Add the Dark Matter tile layer
    folium.TileLayer(
        tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
        name="Stadia Alidade Smooth Dark",
        control=True,
        overlay=False,
    ).add_to(m)

    if st.session_state["marker"]:
        folium.Marker(st.session_state["marker"]).add_to(m)

    output = st_folium(m, width=400, height=400, returned_objects=["last_clicked"])

    if output["last_clicked"]:
        clicked_lat = output["last_clicked"]["lat"]
        clicked_lon = output["last_clicked"]["lng"]

        # Check if the clicked location is different from the current marker
        if st.session_state["marker"] != (clicked_lat, clicked_lon):
            reset_map_and_data()
            st.session_state["marker"] = (clicked_lat, clicked_lon)
            st.session_state["map_center"] = [clicked_lat, clicked_lon]

            api_result = make_api_call(clicked_lat, clicked_lon)
            st.session_state["api_result"] = api_result

            # Update rainfall_data in session state
            rainfall_df = parse_rainfall_data(api_result)
            st.session_state["rainfall_data"] = rainfall_df["Rainfall"].tolist()

            st.rerun()

with col2:
    st.subheader("Hex-Similarity Map")

    # Generate HTML content with the updated rainfall data and fixed New York center
    html_content = generate_html_content(
        st.session_state["rainfall_data"],
        st.session_state["iframe_center"][0],
        st.session_state["iframe_center"][1],
    )

    # Encode the HTML content
    encoded_content = base64.b64encode(html_content.encode()).decode()

    # Display the iframe with the dynamically generated content
    st.components.v1.iframe(
        f"data:text/html;base64,{encoded_content}",
        width=400,
        height=400,
        scrolling=True,
    )

# Display rainfall plot spanning both columns
if st.session_state["marker"]:
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
    plot_df = pd.DataFrame(
        {"Month": months, "Rainfall": st.session_state["rainfall_data"]}
    )
    fig = px.bar(
        plot_df,
        x="Month",
        y="Rainfall",
        title="Monthly Rainfall for Selected Location",
    )
    fig.update_layout(height=400)  # Increased height for better visibility
    st.plotly_chart(fig, use_container_width=True)
