DESCRIPTION
===========

This is the user guide for our final project for CSE 6242 - the carbon emissions calculator.
To simply execute the script, you may skip the steps below and navigate to prediction.godeau.xyz - we have temporarily hosted the website with full functionality for ease of use. Note that query results (the tables and plots) may take a few seconds to populate with results based on the computation.

The main folders of the package are:
1. /CODE/Air traffic data:
	-This folder containes the datasets used for the project under the subfolder 'Yearly traffic'. 
	-The remaining csv files (aircraft_code_final.csv, fuel_consumption.csv and us_airports.csv) are auxiliary datasets to be used for the project, and help us find out the type of aircraft used, amount of fuel consumed in each aircraft and a list of airport codes with geographic coordinates.

2. /CODE/predictions:
	-This folder contains the main backend portion of the project. It includes a routine for filtering out necessary information from the dataset in the select_rows() function under prediction.py. 
	-It also consists code to compute the fuel consumption along a route and carbon emissions, along with the framework for the autoregressive (AR) model used to predict emissions and traffic for future years.

3. /CODE/static:
	-This folder contains the front-end implementation of the project. d3 files are included as a part of the data visualization (d3.min.js and d3-simple-slider.min.js), along with the custom css and js file for our implementation.

4. /CODE/templates:
	-This folder contains the html file that calls the .js and .css files present in /CODE/static when run in a browser.

INSTALLATION
============

Requirements
------------
* Python 3
* virtualenv
* pip

Setup
-----

First of all, go in the "CODE" folder and create a python virtual environment with "virtualenv venv/" and activate it with this command: "source venv/bin/activate".
Then, install the python dependencies with pip: "pip install -r requirements.txt".

The main Python dependencies for the backend are:
click==7.1.1
cycler==0.10.0
Flask==1.1.2
itsdangerous==1.1.0
Jinja2==2.11.1
kiwisolver==1.2.0
MarkupSafe==1.1.1
matplotlib==3.2.1
numpy==1.18.2
pandas==1.0.3
pyparsing==2.4.7
python-dateutil==2.8.1
python-dotenv==0.13.0
pytz==2019.3
six==1.14.0
Werkzeug==1.0.1

Later versions of the above packages may also work, but have not been tested by us.

Then you will need two things:
* Create a Google Cloud Platform API Key with an access to the "Maps Javascript API", "Directions API" and "Places API". (Help: https://developers.google.com/maps/gmp-get-started)
* Create a ".env" file in the project root with the template given in ".env.template". You will need to copy your freshly created API Key between the quotes.

EXECUTION
=========

Now you can start the server by running the following command: "export FLASK_APP=server.py flask run" in aterminal. If everything went find you should be able to access the platform at your local address: "http://127.0.0.1:5000/".

Again, to aid the grading of the project, we have temporarily hosted the project on the website prediction.godeau.xyz
