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

    # NOTE: This hacky as fuck. It seems that the coordinates are mixed up in the csv file
    origin_geolocation      = (data["origin"]["geolocation"]["lng"],      data["origin"]["geolocation"]["lat"])
    destination_geolocation = (data["destination"]["geolocation"]["lng"], data["destination"]["geolocation"]["lat"])

    city_pairs = get_ap_codes(app.all_airports, origin_geolocation, destination_geolocation)

    print(city_pairs)

    result = generate_statistics_for_request(city_pairs, app.data_by_year)

    return json.jsonify(result)
