import streamlit as st
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.title("TaxiFareModel front")

st.markdown("""
Remember that there are several ways to output content into your web page...

Either as with the title by just creating a string (or an f-string). Or as with this paragraph using the `st.` functions
""")

# --- Input Parameters ---
st.header("Enter ride parameters")

pickup_datetime = st.datetime_input(
    "Pickup date and time",
    value=datetime(2023, 1, 1, 12, 0),
)

p_long = st.number_input(
    "Pickup longitude", value=-73.95, step=0.001, format="%.4f"
)
p_lat = st.number_input(
    "Pickup latitude", value=40.7680, step=0.001, format="%.4f"
)
d_long = st.number_input(
    "Dropoff longitude", value=-73.9500, step=0.001, format="%.4f"
)
d_lat = st.number_input(
    "Dropoff latitude", value=40.6500, step=0.001, format="%.4f"
)

passenger_count = st.slider("Passenger count", 1, 6, 1)

# --- Prediction ---
# remeber to go back to previous api code and run
# Load env vars for that project
# export $(grep -v '^#' .env | xargs)
# Run the API locally
# uvicorn taxifare.api.fast:app --reload
url = "http://127.0.0.1:8000/predict"  # your local API

st.header("Prediction result")

# Initialize session state for result and error
if "last_fare" not in st.session_state:
    st.session_state.last_fare = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

if st.button("Predict Fare"):
    params = {
        "pickup_datetime": pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_longitude": p_long,
        "pickup_latitude": p_lat,
        "dropoff_longitude": d_long,
        "dropoff_latitude": d_lat,
        "passenger_count": passenger_count,
    }

    st.write("Request params:", params)

    try:
        response = requests.get(url, params=params)
        st.write("Status code:", response.status_code)
        st.write("Raw response:", response.text)

        response.raise_for_status()
        data = response.json()          # {"fare": ...}
        prediction = float(data["fare"])

        # Store result in session_state so it survives reruns
        st.session_state.last_fare = prediction
        st.session_state.last_error = None

        # Optional: show full JSON below
        st.json(data)

    except Exception as e:
        st.session_state.last_error = str(e)
        st.session_state.last_fare = None

# Always render the result box based on session_state
if st.session_state.last_fare is not None:
    st.success(f"Predicted taxi fare: ${st.session_state.last_fare:.2f}")
elif st.session_state.last_error is not None:
    st.error(f"Error while calling API: {st.session_state.last_error}")
else:
    st.info("Click 'Predict Fare' to see the fare here.")

# --- Map View ---
st.header("Route Map 🗺️")

center_lat = (p_lat + d_lat) / 2
center_long = (p_long + d_long) / 2

m = folium.Map(location=[center_lat, center_long], zoom_start=12)

folium.Marker(
    [p_lat, p_long],
    popup="🟢 Pickup",
    tooltip="Pickup location",
    icon=folium.Icon(color="green"),
).add_to(m)

folium.Marker(
    [d_lat, d_long],
    popup="🔴 Dropoff",
    tooltip="Dropoff location",
    icon=folium.Icon(color="red"),
).add_to(m)

folium.PolyLine(
    [[p_lat, p_long], [d_lat, d_long]],
    color="blue",
    weight=5,
    opacity=0.7,
).add_to(m)

st_folium(m, width=700, height=400, use_container_width=True)

st.markdown("""
**Next steps:**
1. Replace `url` with your production API.
2. Test with `streamlit run app.py`.
3. Deploy: GitHub → Streamlit Cloud or Vercel (add `requirements.txt`).
""")
