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
# LOCAL
# remeber to go back to previous api code and run
# Load env vars for that project
# export $(grep -v '^#' .env | xargs)
# Run the API locally
# uvicorn taxifare.api.fast:app --reload
# or
'''
gcloud run services describe taxifare-api \
  --region europe-west1 \
  --format "value(status.address.url)"

'''

# GCLOUD API DEPLOYMENT
'''
text
# FastAPI on Cloud Run + Streamlit Frontend

This doc summarizes how to:

- Deploy your **FastAPI** taxifare API to **Google Cloud Run**.
- Point your **Streamlit** frontend to the deployed API.
- Keep the predicted fare visible in the UI with `st.session_state`.

---

## 1. Rebuild and Push the API Image to Artifact Registry

From the root of your `data-fast-api` project (where `Dockerfile`, `requirements.txt`, `.env` live):

### 1.1 Load environment variables

Make sure your environment variables are loaded (you should already have `.env` from the challenge):

```bash
direnv reload   # or just open a new shell where direnv is active
You should have at least:

GCP_PROJECT

GCP_REGION (e.g. europe-west1 or us-central1)

GAR_IMAGE (e.g. taxifare)

GAR_MEMORY (e.g. 2Gi)

1.2 Configure Docker auth for Artifact Registry
bash
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
1.3 Build the Cloud Run–compatible image
From the same project root:

bash
docker build \
  --platform linux/amd64 \
  -t $GCP_REGION-docker.pkg.dev/$GCP_PROJECT/taxifare/$GAR_IMAGE:prod .
The --platform linux/amd64 ensures the image matches Cloud Run’s CPU architecture.

1.4 Push the image to Artifact Registry
bash
docker push $GCP_REGION-docker.pkg.dev/$GCP_PROJECT/taxifare/$GAR_IMAGE:prod
You can then see it in the GCP console under Artifact Registry.

2. Deploy the Image to Google Cloud Run
You should already have a .env.yaml as described in the README, containing all required environment variables for the container.

Deploy the service:

bash
gcloud run deploy $GAR_IMAGE \
  --image $GCP_REGION-docker.pkg.dev/$GCP_PROJECT/taxifare/$GAR_IMAGE:prod \
  --memory $GAR_MEMORY \
  --region $GCP_REGION \
  --platform managed \
  --allow-unauthenticated \
  --env-vars-file .env.yaml
Notes:

$GAR_IMAGE is likely taxifare, so the service will be named taxifare.

At the end of the command, you’ll see a line like:

text
Service URL: https://taxifare-xxxxx-ew.a.run.app
Copy that Service URL. This is your public FastAPI endpoint.

You can list services later with:

bash
gcloud run services list --platform=managed --region=$GCP_REGION
3. Sanity Check the Deployed API
Before wiring Streamlit, test the Cloud Run API in the browser or with curl.

Example URL:

text
https://taxifare-xxxxx-ew.a.run.app/predict?pickup_datetime=2014-07-06+19:18:00&pickup_longitude=-73.950655&pickup_latitude=40.783282&dropoff_longitude=-73.984365&dropoff_latitude=40.769802&passenger_count=2
'''

url = "https://taxifare-552184554264.us-central1.run.app/predict"  # your glocud api API

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
