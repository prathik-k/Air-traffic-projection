var map;
var directionsServices;
var directionsRenderer;
var placesService;

const URL = "http://127.0.0.1:5000/statistics";

let statisticsData = null;

const doubleSliderSvg = d3.select("#double_slider")
      .attr("width", 500)
      .attr("height", 50);

let doubleSlider     = null;
let doubleSliderStep = null;

const svgWidth  = (window.innerWidth - 20) / 2;
const svgHeight = 400;

const graphWidth  = 0.7 * svgWidth;
const graphHeight = 0.7 * svgHeight;

const peopleGraphSvg = d3.select("#graph_div")
      .append("svg")
      .attr("width", svgWidth)
      .attr("height", svgHeight);

const emissionGraphSvg = d3.select("#graph_div")
    .append("svg")
    .attr("width", svgWidth)
    .attr("height", svgHeight);

let peopleGraph   = null;
let emissionGraph = null;

let peopleDiv = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

let emissionDiv = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

function cleanData(data) {
    return newData = data.map(d => {
	return {
	    ...d,
	    year: new Date(Date.UTC(d.year)),
	    per_person: parseFloat(d.carbon_emission) / parseFloat(d.number_of_people),
	};
    });
}

function sortData(data) {
    return data.sort((a, b) => {
	return a.year - b.year;
    });
}

function filterData(data, start, end) {
    let newData = [];
    data.forEach(d => {
	if (d.year.getUTCFullYear() >= start && d.year.getUTCFullYear() <= end) {
	    newData.push(d);
	}
    });
    return newData;
}

function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
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
	    //"Access-Control-Allow-Origin": "0.0.0.0:5000",
	},
	body: JSON.stringify(requestData),
    }).then(response => {
	if (!response.ok) {
	    throw new Error("Bad response");
	}
	return response.json();
    });
}

function drawGraphs(data) {
    if (!data) return;
    if (doubleSliderStep.value()[0] == doubleSliderStep.value()[1]) return;
    let filteredData = filterData(data, doubleSliderStep.value()[0], doubleSliderStep.value()[1]);

    drawPeopleGraph(data, filteredData);
    drawEmissionGraph(data, filteredData);
}

function drawPeopleGraph(data, filteredData) {
    const xScale = d3.scaleTime()
	  .domain([
	      d3.min(data, (d) => { return d.year; }),
	      d3.max(data, (d) => { return d.year; })
	  ])
	  .range([0, graphWidth])
	  .nice();

    const yScale = d3.scaleLinear()
	  .domain([
	      0,
	      d3.max(data, (d) => { return d.number_of_people; })
	  ])
	  .range([graphHeight, 0])
	  .nice();

    if (peopleGraph) {
	peopleGraph.remove();
    }

    peopleGraph = peopleGraphSvg.append("g")
	.attr("transform", `translate(${(svgWidth - graphWidth) / 2}, ${(svgHeight - graphHeight) / 2})`);

    let xAxis = peopleGraph.append("g")
	.attr("transform", `translate(0, ${graphHeight})`)
	.call(d3.axisBottom(xScale));

    let yAxis = peopleGraph.append("g")
	.call(d3.axisLeft(yScale));

    let line = d3.line()
	.x((d) => { return xScale(d.year); })
	.y((d) => { return yScale(d.number_of_people); })
	.curve(d3.curveMonotoneX);

    peopleGraph.append("path")
	.datum(filteredData)
	.attr("class", "curve people")
	.attr("d", line);

    peopleGraph.append("path")
	.datum(data)
	.attr("class", "curve_hint people")
	.attr("d", line);

    peopleGraph.selectAll(".people_dots")
	.data(filteredData)
	.enter()
	.append("circle")
	.attr("cx", d => { return xScale(d.year); })
	.attr("cy", d => { return yScale(d.number_of_people); })
	.attr("r", "5px")
	.attr("class", d => {
	    if (d.prediction) {
		return "people_dots_prediction";
	    }
	    return "people_dots";
	})
	.on("mouseover", function(d) {
	    d3.select(this).attr("r", "7px");
	    const leftPosition = d3.event.pageX - 100;
	    const topPosition = d3.event.pageY - 80;
	    peopleDiv.html(`Year: ${d.year.getUTCFullYear()}<br/>Number of people: ${formatNumber(d.number_of_people)}<br/>Carbon Emission: ${formatNumber(d.carbon_emission)} kg<br/>Carbon Emission/Pax: ${d3.format(".2f")(d.per_person)} kg`)
		.style("left", `${leftPosition}px`)
		.style("top", `${topPosition}px`)
		.style("opacity", 1);
	})
	.on("mouseout", function(d) {
	    d3.select(this).attr("r", "5px");
	    peopleDiv.style("opacity", 0);
	});

    let xAxisLabel = peopleGraph.append("text")
	.attr("transform", `translate(${graphWidth / 2}, ${graphHeight + 40})`)
	.style("text-anchor", "middle")
	.text("Year");

    let yAxisLabel = peopleGraph.append("text")
	.attr("transform", "rotate(-90)")
	.attr("y", -70)
	.attr("x", -graphHeight / 2)
	.style("text-anchor", "middle")
	.text("Number of people");
}

function drawEmissionGraph(data, filteredData) {
    const xScale = d3.scaleTime()
	  .domain([
	      d3.min(data, (d) => { return d.year; }),
	      d3.max(data, (d) => { return d.year; })
	  ])
	  .range([0, graphWidth])
	  .nice();

    const yScale = d3.scaleLinear()
	  .domain([
	      0,
	      d3.max(data, (d) => { return d.carbon_emission; })
	  ])
	  .range([graphHeight, 0])
	  .nice();

    if (emissionGraph) {
	emissionGraph.remove();
    }

    emissionGraph = emissionGraphSvg.append("g")
	.attr("transform", `translate(${(svgWidth - graphWidth) / 2}, ${(svgHeight - graphHeight) / 2})`);

    let xAxis = emissionGraph.append("g")
	.attr("transform", `translate(0, ${graphHeight})`)
	.call(d3.axisBottom(xScale));

    let yAxis = emissionGraph.append("g")
	.call(d3.axisLeft(yScale));

    let line = d3.line()
	.x((d) => { return xScale(d.year); })
	.y((d) => { return yScale(d.carbon_emission); })
	.curve(d3.curveMonotoneX);

    emissionGraph.append("path")
	.datum(filteredData)
	.attr("class", "curve emission")
	.attr("d", line);

    emissionGraph.append("path")
	.datum(data)
	.attr("class", "curve_hint emission")
	.attr("d", line);

    emissionGraph.selectAll(".emission_dots")
	.data(filteredData)
	.enter()
	.append("circle")
	.attr("cx", d => { return xScale(d.year); })
	.attr("cy", d => { return yScale(d.carbon_emission); })
	.attr("r", "5px")
	.attr("class", d => {
	    if (d.prediction) {
		return "emission_dots_prediction";
	    }
	    return "emission_dots";
	})
	.on("mouseover", function(d) {
	    d3.select(this).attr("r", "7px");
	    const leftPosition = d3.event.pageX - 100;
	    const topPosition = d3.event.pageY - 80;
	    emissionDiv.html(`Year: ${d.year.getUTCFullYear()}<br/>Number of people: ${formatNumber(d.number_of_people)}<br/>Carbon Emission: ${formatNumber(d.carbon_emission)} kg<br/>Carbon Emission/Pax: ${d3.format(".2f")(d.per_person)} kg`)
		.style("left", `${leftPosition}px`)
		.style("top", `${topPosition}px`)
		.style("opacity", 1);
	})
	.on("mouseout", function(d) {
	    d3.select(this).attr("r", "5px");
	    emissionDiv.style("opacity", 0);
	});

    let xAxisLabel = emissionGraph.append("text")
	.attr("transform", `translate(${graphWidth / 2}, ${graphHeight + 40})`)
	.style("text-anchor", "middle")
	.text("Year");

    let yAxisLabel = emissionGraph.append("text")
	.attr("transform", "rotate(-90)")
	.attr("y", -70)
	.attr("x", -graphHeight / 2)
	.style("text-anchor", "middle")
	.text("Carbon Emission (kg)");
}

searchButton.onclick = function() {
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
		statisticsData = sortData(cleanData(data));
		if (doubleSlider) {
		    doubleSlider.remove();
		}
		doubleSlider = doubleSliderSvg.append("g")
		    .attr("transform", "translate(50, 10)");

		let minYear = d3.min(statisticsData, d => { return d.year.getUTCFullYear(); });
		let maxYear = d3.max(statisticsData, d => { return d.year.getUTCFullYear(); });

		doubleSliderStep = d3.sliderBottom()
		    .min(minYear)
		    .max(maxYear)
		    .width(400)
		    .tickFormat(d3.format("d"))
		    .ticks(maxYear - minYear + 2)
		    .default([minYear, maxYear])
		    .step(1)
		    .fill('#2196f3')
		    .on("onchange", _ => {
			drawGraphs(statisticsData);
		    });
		doubleSlider.call(doubleSliderStep);

		drawGraphs(statisticsData);
	    })
	    .catch(err => { console.error(err); });

	directionsRenderer.setDirections(directions);
	fromInput.value = "";
	toInput.value = "";
    }).catch((err) => {
	console.log(`Error: '${err}'`);
    });
};
