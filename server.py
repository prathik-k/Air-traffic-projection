from flask import Flask
from flask import request, json, render_template
from predictions import prediction
from predictions.prediction import generate_statistics_for_request


app = Flask(__name__)

# Init the app state relative to the prediction model
app = prediction.init_app(app)


@app.route("/")
def index_handler():
    return render_template("index.html")


@app.route("/statistics", methods=["POST"])
def statistics_handler():
    data = request.json

    result = generate_statistics_for_request("ATL", "JFK", app.data_by_year)

    return json.jsonify(result)
