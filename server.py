import sys
import os

from flask import Flask
from flask import request, json, render_template
from predictions import prediction
from predictions.prediction import generate_statistics_for_request
from predictions.get_ap_code import get_ap_codes
from predictions.fuel_consumption import other_transport
from dotenv import load_dotenv
load_dotenv()

if os.getenv("GMAPS_API_KEY") is None:
    sys.exit(-1)

app = Flask(__name__)

# Init the app state relative to the prediction model
app = prediction.init_app(app)


@app.route("/")
def index_handler():
    return render_template("index.html", api_key=os.getenv("GMAPS_API_KEY"))


@app.route("/statistics", methods=["POST"])
def statistics_handler():
    data = request.json

    origin_geolocation      = (data["origin"]["geolocation"]["lat"],      data["origin"]["geolocation"]["lng"])
    destination_geolocation = (data["destination"]["geolocation"]["lat"], data["destination"]["geolocation"]["lng"])

    city_pairs = get_ap_codes(app.all_airports, origin_geolocation, destination_geolocation)
    result = generate_statistics_for_request(city_pairs, app.data_by_year, app.coefs_of_dot_codes)

    car_emissions, train_emissions = other_transport(data["distance"])

    result = {
        "planes": result,
        "cars": car_emissions,
        "train": train_emissions,
    }

    return json.jsonify(result)
