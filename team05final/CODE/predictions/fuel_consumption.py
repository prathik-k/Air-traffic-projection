import numpy as np
import matplotlib.pyplot as plt


def compute_distances_vector_in_miles(iata_to_fuel):
    """
    This function converts distance from nautical miles to miles.
    :param iata_to_fuel: Data mapping fuel consumption to aircraft IATA codes
    :return x_miles: Array containing distances in miles
    """
    # From the data mapping fuel consumption to aircraft IATA codes we get distances in nautical miles.
    x_nautical_miles = np.array(iata_to_fuel.keys()[1:]).astype(float)
    # We convert these distances in nautical miles to distances in miles.
    x_miles = x_nautical_miles * 1.15078  # 1 nautical mile = 1.15078 mile

    return x_miles


def compute_polynomial_coefficients(x, y, degree):
    """
    This function computes the coefficients of a polynomial regression model.
    :param x: Array representing the input values.
    :param y: Array representing the output values.
    :param degree: Integer representing the degree of the polynomial model.
    :return coefficients: Array containing the coefficients of the polynomial model.
    """
    coefficients = np.polyfit(x, y, degree)

    return coefficients


def get_flight_distance(origin, dest, year, data_by_year):
    """
    #his function computes flight distance between an origin and a destination.
    :param origin: String representing the three-letter code of the origin airport.
    :param dest: String representing the three-letter code of the destination airport.
    :param year: Year of the data that we wish to work with.
    :param data_by_year: Data corresponding to yearly air trafic.
    :return distance_in_miles: Float representing the flight distance in miles between the origin and the destination.
    """
    distance_in_miles = np.array(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['DISTANCE'])[0]

    return distance_in_miles


def compute_definitive_coefficients(data_by_year, dot_to_iata, iata_to_fuel, degree=4):
    """
    This function returns the coefficients of polynomial models used to compute the fuel consumption of all the different
    aircrafts.
    The fuel consumption depends a lot on the type of aircrafts. The iata_to_fuel data maps fuel consumption to aircraft
    IATA codes in an undirect manner. For each aircraft it returns its fuel consumption for some given distances.
    We thus approximate the fuel consumption model of each aircraft using these values.

    :param data_by_year: Data corresponding to yearly air trafic.
    :param dot_to_iata: Data mapping aicraft DOT codes to aircraft IATA codes. Also provides the number of seats of
    each aircraft.
    :param iata_to_fuel: Data mapping fuel consumption to aircraft IATA codes.
    :param degree: Degree of the polynomial model
    :return coefs_of_dot_codes: Dictionary containing the polynomial fuel consumption model of different aircrafts.
    """
    coefs_of_dot_codes = {}  # Initialization of the dictionary containing the polynomial model of different aircrafts.

    x_miles = compute_distances_vector_in_miles(iata_to_fuel)  # Distances present in the iata_to_fuel data
    dot_codes_used = []

    # We look at all the aircrafts that were used between the years 2015 and 2019. We only list the aircrafts thave have
    # been used during these years and not between the years 2005 to 2019 for instance because we had to map by hand
    # the dot codes of the aircraft present in the data_by_year data to the iata codes of the aircraft present in the
    # iata_to_fuel. Since it was time consuming we decided to only list aircrafts used between 2015 and 2019 and assumed
    # that they were representative of the aircrafts used between 2005 and 2019.
    years = ['2015', '2016', '2017', '2018', '2019']
    for yr_str in years:
        dot_codes_used += list(data_by_year[yr_str]['AIRCRAFT_TYPE'])

    # We get a list of the dot codes of all the aircrafts used between 2015 and 2019
    dot_codes = np.unique(dot_codes_used)
    for k in range(len(dot_codes)):
        # For each aircraft (represented by a dot code) we get its corresponding iata code
        iata_code = np.array(dot_to_iata.iloc[np.where(dot_to_iata['DOT'] == dot_codes[k])]['IATA'])[0]
        # We also get the number of seats associated to this aircraft
        seats_nb = np.array(dot_to_iata.iloc[np.where(dot_to_iata['DOT'] == dot_codes[k])]['Seats'])[0]
        coefs_of_dot_codes[dot_codes[k]] = {"seats": seats_nb, "coefs": None}

        # If this iata code is associated to its fuel consumption in the iata_to_fuel data:
        if len(iata_to_fuel.iloc[np.where(iata_to_fuel['IATA'] == iata_code)]) != 0:
            # We get the fuel consumption values of this particular aircraft for the distances present in x_miles
            y = np.array(iata_to_fuel.iloc[np.where(iata_to_fuel['IATA'] == iata_code)])[0][1:]
            y = np.array(y, dtype=float)
            y = y[~np.isnan(y)]  # We get rid of the values associated to nan values
            # We use the distances present in x_miles and the associated fuel consumption of this aircraft to compute
            # a polynomial model for the fuel consumption of this aircraft.
            coefs = compute_polynomial_coefficients(x_miles[:len(y)], y, degree)
            # We store the parameters of this model for this particular aircraft in the final dictionary
            coefs_of_dot_codes[dot_codes[k]]["coefs"] = coefs

    # We gather all the parameters of the different models associated to the fuel consumption of the different aircrafts
    # into one list called all_coefs
    all_coefs = []
    for sub in coefs_of_dot_codes:
        if ((coefs_of_dot_codes[sub]["coefs"]) is not None):
            all_coefs.append(coefs_of_dot_codes[sub]["coefs"])

    # We add a special key/value pair to the final dictionary which will be used if we later have to deal with an aircraft
    # code for which we do not have any fuel consumption model or which was not listed in the original list of the
    # aircrafts used during years 2015-2019.
    # The model associated to this special key is made of coefficients which are an average of the coefficients of all
    # the other models.
    # The number of seat associated to this special key are an average of the number of seats of all the other aircrafts.
    coefs_of_dot_codes[0] = {"coefs": np.mean(all_coefs, axis=0),
                             "seats": np.mean([coefs_of_dot_codes[sub]["seats"] for sub in coefs_of_dot_codes], axis=0)}

    return coefs_of_dot_codes


def compute_CO2_emissions(origin, dest, year, data_by_year, coefs_of_dot_codes):
    """
    This function computes the CO2 emission by calculating the fuel consumption, and using a standard conversion from kg of fuel to kg of CO2 produced.
    :param origin: String representing the three-letter code of the origin airport.
    :param dest: String representing the three-letter code of the destination airport.
    :param year: Year of the data that we wish to work with.
    :param data_by_year: Data corresponding to yearly air trafic.
    :param coefs_of_dot_codes: Dictionary containing the polynomial fuel consumption model of different aircrafts.
    :return CO2_kg: Float representing the carbon emission produced by all the flights that flew between a particular
    origin and a particular destination during a particular year.
    """
    # We get the distance in miles between the origin airport and the destination airport
    flight_distance = get_flight_distance(origin, dest, year, data_by_year)

    # We get the dot codes of all the aircrafts that have been flying between this origin and this destination during this
    # particular year
    dot_codes = np.array(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['AIRCRAFT_TYPE'])

    # We get the number of seats of all the aircrafts that have been flying between this origin and this destination during
    # this particular year
    seats_nb = np.array(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['PASSENGERS'])
    fuel_total_consumption_kg = 0  # Initialization of the fuel consumption

    # We go through all the flights which took place between this origin and this destination during this particular
    # year
    for k in range(len(dot_codes)):
        # If the type of aircraft is not part of types of aircrafts which have been used between 2015 and 2019
        if dot_codes[k] not in coefs_of_dot_codes:
            # We use parameters which are an average of the parameters of all the other aircrafts for the model of this
            # aircraft
            coefs = coefs_of_dot_codes[0]["coefs"]
            # We use the number of seats which is an average of the number of seats of all the other aircrafts.
            # We estimate the number of flights which took place between this origin and this destination for this year.
            # Indeed each row of the data_by_year data corresponds to monthly statistics. Therefore to compute the exact
            # number of flights which took place during a year we divide the number of seats present in this row by the
            # number of seats of this type of aircraft.
            estimated_number_of_flights = int(round((seats_nb[k]) / (coefs_of_dot_codes[0]["seats"])))

        # If the type of aircraft is part of the types of aircrafts which have been used between 2015 and 2019 but its
        # code is not associated to any fuel consumption values
        elif coefs_of_dot_codes[dot_codes[k]]["coefs"] is None:
            # We use parameters which are an average of the parameters of all the other aircrafts for the model of this
            # aircraft
            coefs = coefs_of_dot_codes[0]["coefs"]
            # We use the number of seats of this particular aircraft.
            estimated_number_of_flights = int(round((seats_nb[k]) / (coefs_of_dot_codes[dot_codes[k]]["seats"])))

        else:
            # We use the fuel consumption model of this specific type of aircraft
            coefs = coefs_of_dot_codes[dot_codes[k]]["coefs"]
            # We use the number of seats of this specific type of aircraft
            estimated_number_of_flights = int(round((seats_nb[k]) / (coefs_of_dot_codes[dot_codes[k]]["seats"])))

        # We use the fuel consumption model and apply it on the distance to compute the fuel consumed by this type of
        # aircraft on this distance.
        fuel_consumed_for_distance = np.polyval(coefs, flight_distance)
        # We multiply the fuel consumed by this type of aircraft on this distance with the number of flights of this kind
        # which flew between this origin and this destination at this particular year.
        fuel_total_consumption_kg += fuel_consumed_for_distance * estimated_number_of_flights

    # We convert the fuel consumption in kg to CO2 consumption in kg
    CO2_kg = round(fuel_total_consumption_kg * 3.15)

    return CO2_kg


def plot_aircraft_codes_histogram(data_by_year):
    """
    This is an accessory function to obtain the most commonly used aircraft for flights, and plot a histogram of aircraft
    types used for all flights.
    :param data_by_year: Data corresponding to yearly air trafic.
    :return: A graph displaying a histogram of the types of aircraft used for all flights for the years present in data_by_year
    """
    years_str = list(data_by_year.keys())

    # We get a list of all the types of aircrafts that flew during the years present in data_by_year
    dot_codes_used = []
    for yr_str in years_str:
        dot_codes_used += list(data_by_year[yr_str]['AIRCRAFT_TYPE'])
    dot_codes_used = np.array(dot_codes_used)

    # We get a list containing all these different types of aircrafts only once
    dot_codes = np.unique(dot_codes_used)

    plt.title("Types of aircrafts used between 2015 and 2019")
    plt.xlabel("DOT Aircraft code")
    plt.ylabel("Number of flights done")
    plt.hist(dot_codes_used, dot_codes)
    plt.show()


def other_transport(dist):
    """
    This function returns the average CO2 emitted per person on a certain distance for different types of cars and for
    trains.
    Uses average mileage for all cars classified by category (according to EPA classification). Estimates mileage from
    distance between cities.
    Train fuel economy on a passenger-miles per gallon basis on a national average AMTRAK load factor of 54.6%.
    :param dist: Float representing a distance in miles
    :return car_fuel_emissions, train_avg: Two dictionaries with CO2 emission per person for each type of car and train.
    """
    car_fuel_emissions = {'Two-seater': 22, 'Subcompact': 24, 'Compact': 26, 'Midsize Sedan': 26, 'Large Sedan': 21,
                          'Hatchback': 27, 'Pickup truck': 18, 'Minivan': 20, 'Small SUV': 24, 'Standard SUV': 18}
    car_fuel_emissions.update({i: 9.07185 * (dist / car_fuel_emissions[i]) for i in car_fuel_emissions.keys()})

    car_fuel_emissions = [{"type": key, "emissions": value} for key, value in car_fuel_emissions.items()]

    train_avg = [{"type": "Train", "emissions": 10.1514 * (dist / 71.6)}]

    return (car_fuel_emissions, train_avg)
