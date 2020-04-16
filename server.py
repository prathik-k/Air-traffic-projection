from flask import Flask
from flask import request, json, render_template
from predictions import prediction
from predictions.prediction import generate_statistics_for_request
from predictions.get_ap_code import get_ap_codes


app = Flask(__name__)

# Init the app state relative to the prediction model
app = prediction.init_app(app)


@app.route("/")
def index_handler():
    return render_template("index.html")


@app.route("/statistics", methods=["POST"])
def statistics_handler():
    data = request.json

    origin_geolocation      = (data["origin"]["geolocation"]["lat"],      data["origin"]["geolocation"]["lng"])
    destination_geolocation = (data["destination"]["geolocation"]["lat"], data["destination"]["geolocation"]["lng"])

    city_pairs = get_ap_codes(app.all_airports, origin_geolocation, destination_geolocation)

<<<<<<< HEAD
    result = generate_statistics_for_request(city_pairs, app.data_by_year, app.coefs_of_dot_codes)
=======
    result = generate_statistics_for_request(city_pairs, app.data_by_year, app.dot_to_iata, app.iata_to_fuel)
>>>>>>> f3de296ebf2bd84d14efbfe3f0d7051aed4ce946

    return json.jsonify(result)
