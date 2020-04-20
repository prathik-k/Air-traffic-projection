# DVA-Project
CSE 6242 Final Project - Calculating/projecting the carbon footprint of air travel.

# Requirements
* Python 3
* virtualenv
* pip

# Installation

First of all, create a python virtual environment with `virtualenv venv/` and activate it with this command: `source .env/bin/activate`.
Then, install the python dependencies with pip: `pip install -r requirements.txt`.

Then you will need two things:
* Create a Google Cloud Platform API Key with an access to the `Maps Javascript API`, `Directions API` and `Places API`. (Help: [Google Help](https://developers.google.com/maps/gmp-get-started))
* Create a `.env` file in the project root with the template given in `.env.template`. You will need to copy your freshly created API Key between the quotes.

Then you can start the server by running the following command: `export FLASK_APP=server.py flask run`. If everything went find you should be able to access the platform at your local address: `http://127.0.0.1:5000/`.
