var map;
var directionsServices;
var directionsRenderer;
var placesService;

const URL = "http://127.0.0.1:5000/statistics";
const METERS_TO_MILES = 0.000621371;

let statisticsData = null;

const sliderWidth = 700;
const sliderMargin = 30;
const sliderTextWidth = 130;
const sliderTextMargin = 20;

let doubleSliderStep = null;

const peopleColor = "#B32300";
const emissionColor = "#2100FA";
const peoplePredictionColor = "#B37C6F";
const emissionPredictionColor = "#8E7DFA";

const svgWidth = window.innerWidth - 20;
const svgHeight = 400;

const svgGraphWidth  = svgWidth * 0.4;
const svgGraphHeight = svgHeight;

const graphLeftAxisWidth = 70;
const graphBottomAxisHeight = 40;

const graphMargin = {
    top: 40,
    bottom: graphBottomAxisHeight + 20,
    left: graphLeftAxisWidth + 20,
    right: 20,
};

const graphWidth  = svgGraphWidth - graphMargin.left - graphMargin.right;
const graphHeight = svgGraphHeight - graphMargin.top - graphMargin.bottom;

const legendWidth = svgWidth * 0.2;
const legendHeight = svgHeight;

let graphDiv = null;
let sliderDiv = null;
let noDataDiv = null;

let peopleDiv = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

let emissionDiv = d3.select("body")
    .append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

let carTable = null;
let trainTable = null;

const otherTransportTable = d3.select("#other_transport_table");

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

function getFirstPredictionData(sortedData) {
    return sortedData.find(d => { return d.prediction; });
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

function makeRequestData(directions, originDetails, destinationDetails) {
    return {
	origin: getCityAndGeolocation(originDetails),
	destination: getCityAndGeolocation(destinationDetails),
	distance: directions.routes[0].legs[0].distance.value * METERS_TO_MILES,
    };
}

function getTripStatistics(requestData) {
    return fetch(URL, {
	method: "POST",
	mode: "cors",
	headers: {
	    "Content-Type": "application/json",
	},
	body: JSON.stringify(requestData),
    }).then(response => {
	if (!response.ok) {
	    throw new Error("Bad response");
	}
	return response.json();
    });
}

function removeGraphs() {
    if (graphDiv) {
	graphDiv.remove();
    }
}

function drawGraphs(data) {
    if (!data) return;
    if (doubleSliderStep.value()[0] == doubleSliderStep.value()[1]) return;
    let filteredData = filterData(data, doubleSliderStep.value()[0], doubleSliderStep.value()[1]);

    removeGraphs();
    graphDiv = d3.select("body").append("div").attr("class", "graph_div");

    drawPeopleGraph(data, filteredData);
    drawLegend();
    drawEmissionGraph(data, filteredData);
}

function drawPeopleGraph(data, filteredData) {
    const firstPrediction = getFirstPredictionData(data);
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

    let peopleGraphSvg = graphDiv
	.append("svg")
	.attr("width", svgGraphWidth)
	.attr("height", svgGraphHeight);

    let peopleGraph = peopleGraphSvg.append("g")
	.attr("transform", `translate(${graphMargin.left}, ${graphMargin.top})`);

    let xAxis = peopleGraph.append("g")
	.attr("transform", `translate(0, ${graphHeight})`)
	.call(d3.axisBottom(xScale));

    let yAxis = peopleGraph.append("g")
	.call(d3.axisLeft(yScale));

    let predictionZone = peopleGraph.append("rect")
	.attr("width", xScale.range()[1] - xScale(firstPrediction.year))
	.attr("height", graphHeight)
	.attr("x", xScale(firstPrediction.year))
	.attr("class", "people_prediction_zone");

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
	.attr("transform", `translate(${graphWidth / 2}, ${graphHeight + graphBottomAxisHeight})`)
	.style("text-anchor", "middle")
	.text("Year");

    let yAxisLabel = peopleGraph.append("text")
	.attr("transform", "rotate(-90)")
	.attr("y", -graphLeftAxisWidth)
	.attr("x", -graphHeight / 2)
	.style("text-anchor", "middle")
	.text("Number of people");

    let graphTitle = peopleGraph.append("text")
	.attr("transform", `translate(${graphWidth / 2}, -10)`)
	.style("text-anchor", "middle")
	.attr("class", "graph_title")
	.text("Evolution of carbon emissions over the year");
}

function drawEmissionGraph(data, filteredData) {
    const firstPrediction = getFirstPredictionData(data);
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

    let emissionGraphSvg = graphDiv
	.append("svg")
	.attr("width", svgGraphWidth)
	.attr("height", svgGraphHeight);

    let emissionGraph = emissionGraphSvg.append("g")
	.attr("transform", `translate(${graphMargin.left}, ${graphMargin.top})`);

    let xAxis = emissionGraph.append("g")
	.attr("transform", `translate(0, ${graphHeight})`)
	.call(d3.axisBottom(xScale));

    let yAxis = emissionGraph.append("g")
	.call(d3.axisLeft(yScale));

    let predictionZone = emissionGraph.append("rect")
	.attr("width", xScale.range()[1] - xScale(firstPrediction.year))
	.attr("height", graphHeight)
	.attr("x", xScale(firstPrediction.year))
	.attr("class", "emission_prediction_zone");

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
	.attr("transform", `translate(${graphWidth / 2}, ${graphHeight + graphBottomAxisHeight})`)
	.style("text-anchor", "middle")
	.text("Year");

    let yAxisLabel = emissionGraph.append("text")
	.attr("transform", "rotate(-90)")
	.attr("y", -graphLeftAxisWidth)
	.attr("x", -graphHeight / 2)
	.style("text-anchor", "middle")
	.text("Carbon Emission (kg)");

    let graphTitle = emissionGraph.append("text")
	.attr("transform", `translate(${graphWidth / 2}, -10)`)
	.style("text-anchor", "middle")
	.attr("class", "graph_title")
	.text("Evolution of passenger transported over the year");
}

function drawLegend() {
    let legendSvg = graphDiv
	.append("svg")
	.attr("width", legendWidth)
	.attr("height", legendHeight);

    const legendData = [
	{ title: "Number of people", color: peopleColor },
	{ title: "Prediction of the number of people", color: peoplePredictionColor },
	{ title: "Carbon emissions", color: emissionColor },
	{ title: "Prediction for the carbon emissions", color: emissionPredictionColor },
    ];

    const rightMargin = 10;

    const offset = 30;
    let currentOffset = 20;

    const rectWidth = 25;
    const rectHeight = 15;

    let legend = legendSvg.append("g");

    legendData.forEach((info) => {
	legend.append("rect")
	    .attr("x", rightMargin)
	    .attr("y", currentOffset)
	    .attr("width", rectWidth)
	    .attr("height", rectHeight)
	    .style("fill", info.color);

	legend.append("text")
	    .attr("x", rightMargin * 2 + rectWidth)
	    .attr("y", currentOffset + rectHeight)
	    .text(info.title);

	currentOffset += offset;
    });
}

function cleanTable() {
    if (carTable) {
	carTable.remove();
    }
    if (trainTable) {
	trainTable.remove();
    }

}

function drawOtherTransportTable(data) {
    cleanTable();
    carTable = otherTransportTable.selectAll("tr.cars")
	.data(data.cars)
	.enter()
	.append("tr")
	.attr("class", "cars");

    carTable.append("td").text(d => { return d.type; })
	.style("border-width", function(d, i) {
	    if (i == 0) {
		return "2px 1px 1px 1px";
	    }
	    return "1px";
	});
    carTable.append("td").text(d => { return d3.format(".2f")(d.emissions); })
	.style("border-width", function(d, i) {
	    if (i == 0) {
		return "2px 1px 1px 1px";
	    }
	    return "1px";
	});

    trainTable = otherTransportTable.selectAll("tr.train")
	.data(data.train)
	.enter()
	.append("tr")
	.attr("class", "train");

    trainTable.append("td").text(d => { return d.type; })
	.style("border-width", function(d, i) {
	    if (i == 0) {
		return "2px 1px 1px 1px";
	    }
	    return "1px";
	});
    trainTable.append("td").text(d => { return d3.format(".2f")(d.emissions); })
	.style("border-width", function(d, i) {
	    if (i == 0) {
		return "2px 1px 1px 1px";
	    }
	    return "1px";
	});
}

function removeSlider() {
    if (sliderDiv) {
	sliderDiv.remove();
    }
}

function drawSlider(statisticsData) {
    removeSlider();

    sliderDiv = d3.select("body").append("div");

    let doubleSliderSvg = sliderDiv.append("svg")
	.attr("width", sliderWidth + 2 * sliderMargin + sliderTextWidth + sliderTextMargin)
	.attr("height", 50)
	.attr("class", "#double_slider");

    doubleSliderSvg.append("text")
	.attr("transform", "translate(20, 15)")
	.text("Year range selection:");
    let doubleSlider = doubleSliderSvg.append("g")
	.attr("transform", `translate(${sliderMargin + sliderTextWidth + sliderTextMargin}, 10)`);

    let minYear = d3.min(statisticsData, d => { return d.year.getUTCFullYear(); });
    let maxYear = d3.max(statisticsData, d => { return d.year.getUTCFullYear(); });

    doubleSliderStep = d3.sliderBottom()
	.min(minYear)
	.max(maxYear)
	.width(sliderWidth)
	.tickFormat(d3.format("d"))
	.ticks(maxYear - minYear + 2)
	.default([minYear, maxYear])
	.step(1)
	.fill('#2196f3')
	.on("onchange", _ => {
	    drawGraphs(statisticsData);
	});
    doubleSlider.call(doubleSliderStep);
}

function removeNoDataMessage() {
    if (noDataDiv) {
	noDataDiv.remove();
    }
}

searchButton.onclick = function() {
    removeGraphs();
    removeSlider();
    cleanTable();
    removeNoDataMessage();

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
	let requestData = makeRequestData(directions, originDetails, destinationDetails);

	getTripStatistics(requestData)
	    .then(data => {
		if (data.planes) {
		    statisticsData = sortData(cleanData(data.planes));

		    drawSlider(statisticsData);
		    drawGraphs(statisticsData);
		} else {
		    noDataDiv = d3.select("body").append("div");
		    noDataDiv.append("p").text("No direct flights between the cities specified.");
		}
		drawOtherTransportTable(data);
	    })
	    .catch(err => { console.error(err); });

	directionsRenderer.setDirections(directions);
	fromInput.value = "";
	toInput.value = "";
    }).catch((err) => {
	console.log(`Error: '${err}'`);
    });
};
