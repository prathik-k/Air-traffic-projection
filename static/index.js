var map;
var directionsServices;
var directionsRenderer;
var placesService;

const URL = "http://127.0.0.1:5000/statistics";

const yearRow = d3.select("#year_row");
const numberOfPeopleRow = d3.select("#number_of_people_row");
const carbonEmissionRow = d3.select("#carbon_emission_row");


console.log(yearRow);

function sortData(data) {
    return data.sort((a, b) => {
	return a.year - b.year;
    });
}

function formatNumber(num) {
  return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}

function initMap() {
    directionsServices = new google.maps.DirectionsService();

    map = new google.maps.Map(document.getElementById('map'), {
	center: {lat: -34.397, lng: 150.644},
	zoom: 8
    });

    let rendererOptions = {
	map: map
    };

    directionsRenderer = new google.maps.DirectionsRenderer(rendererOptions);
    placesService = new google.maps.places.PlacesService(map);
}

const fromInput = document.getElementById("from_input");
const toInput = document.getElementById("to_input");
const searchButton = document.getElementById("search_button");
const tripSummary = document.getElementById("trip_summary");

function getPlaceDetailsPromise(request) {
    return new Promise((resolve, reject) => {
	placesService.getDetails(request, (place, status) => {
	    if (status != "OK") return reject(status);
	    resolve(place);
	});
    });
}

function getDirectionsPromise(request) {
    return new Promise((resolve, reject) => {
	directionsServices.route(request, (response, status) => {
	    if (status != "OK") return reject(status);
	    resolve(response);
	});
    });
}

function getCityAndGeolocation(details) {
    let city        = details.address_components.find(element => element.types.includes("locality")).long_name;
    let geolocation = {
	lat: details.geometry.location.lat(),
	lng: details.geometry.location.lng(),
    };

    return {
	city: city,
	geolocation: geolocation,
    };
}

function makeRequestData(originDetails, destinationDetails) {
    return {
	origin: getCityAndGeolocation(originDetails),
	destination: getCityAndGeolocation(destinationDetails),
    };
}

function getTripStatistics(requestData) {
    return fetch(URL, {
	method: "POST",
	mode: "cors",
	headers: {
	    "Content-Type": "application/json",
	    "Access-Control-Allow-Origin": "0.0.0.0:5000",
	},
	body: JSON.stringify(requestData),
    }).then(response => {
	if (!response.ok) {
	    throw new Error("Bad response");
	}
	return response.json();
    });
}

searchButton.onclick = function() {
    yearRow.selectAll("th:not(.label)").remove();
    carbonEmissionRow.selectAll("td:not(.label)").remove();
    numberOfPeopleRow.selectAll("td:not(.label)").remove();
    let request = {
	origin: fromInput.value,
	destination: toInput.value,
	travelMode: "DRIVING"
    };

    getDirectionsPromise(request).then(response => {
	let originPlaceRequest = {
	    placeId: response.geocoded_waypoints[0].place_id,
	    fields: ["geometry", "address_components"],
	};

	let destinationPlaceRequest = {
	    placeId: response.geocoded_waypoints[1].place_id,
	    fields: ["geometry", "address_components"],
	};

	return Promise.all([
	    response,
	    getPlaceDetailsPromise(originPlaceRequest),
	    getPlaceDetailsPromise(destinationPlaceRequest)
	]);
    }).then(([directions, originDetails, destinationDetails]) => {
	let requestData = makeRequestData(originDetails, destinationDetails);

	getTripStatistics(requestData)
	    .then(data => {
		const sortedData = sortData(data);
		yearRow.selectAll("th:not(.label)")
		    .data(sortedData)
		    .enter()
		    .append("th")
		    .text((d) => d.year)
		    .attr("class", (d) => d.prediction ? "prediction" : null);

		numberOfPeopleRow.selectAll("td:not(.label)")
		    .data(sortedData)
		    .enter()
		    .append("td")
		    .text((d) => formatNumber(d.number_of_people))
		    .attr("class", (d) => d.prediction ? "prediction" : null);

		carbonEmissionRow.selectAll("td:not(.label)")
		    .data(sortedData)
		    .enter()
		    .append("td")
		    .text((d) => formatNumber(d.carbon_emission))
		    .attr("class", (d) => d.prediction ? "prediction" : null);
	    })
	    .catch(err => { console.error(err); });

	directionsRenderer.setDirections(directions);
	fromInput.value = "";
	toInput.value = "";
	tripSummary.textContent = directions.routes[0].legs[0].distance.text;
    }).catch((err) => {
	console.log(`Error: '${err}'`);
    });
};
