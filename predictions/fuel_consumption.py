import numpy as np
import matplotlib.pyplot as plt


def compute_distances_vector_in_miles(iata_to_fuel):
    x_nautical_miles = np.array(iata_to_fuel.keys()[1:]).astype(float)
    x_miles = x_nautical_miles * 1.15078  # 1 nautical mile = 1.15078 mile
    return x_miles


def compute_polynomial_coefficients(x, y, degree):
    coefficients = np.polyfit(x, y, degree)
    return coefficients


def get_flight_distance(origin, dest, year, data_by_year):
    distance_in_miles = np.array(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['DISTANCE'])[0]
    return distance_in_miles


def compute_definitive_coefficients(data_by_year, dot_to_iata, iata_to_fuel, degree=4):
    coefs_of_dot_codes = {}

    x_miles = compute_distances_vector_in_miles(iata_to_fuel)
    years_str = list(data_by_year.keys())
    dot_codes_used = []
    for yr_str in years_str:
        dot_codes_used += list(data_by_year[yr_str]['AIRCRAFT_TYPE'])

    dot_codes = np.unique(dot_codes_used)
    for k in range(len(dot_codes)):
        iata_code = np.array(dot_to_iata.iloc[np.where(dot_to_iata['DOT'] == dot_codes[k])]['IATA'])[0]
        if len(iata_to_fuel.iloc[np.where(iata_to_fuel['IATA'] == iata_code)]) != 0:
            y = np.array(iata_to_fuel.iloc[np.where(iata_to_fuel['IATA'] == iata_code)])[0][1:]
            y = np.array(y, dtype=float)
            y = y[~np.isnan(y)]
            coefs = compute_polynomial_coefficients(x_miles[:len(y)], y, degree)
            coefs_of_dot_codes[dot_codes[k]] = coefs

    coefs_of_dot_codes[0] = np.mean(list((coefs_of_dot_codes.values())), axis=0)

    return coefs_of_dot_codes


def compute_CO2_emissions(origin, dest, year, data_by_year, coefs_of_dot_codes):
    flight_distance = get_flight_distance(origin, dest, year, data_by_year)

    dot_codes = np.array(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['AIRCRAFT_TYPE'])
    fuel_total_consumption_kg = 0
    for k in range(len(dot_codes)):
        if dot_codes[k] not in coefs_of_dot_codes:
            coefs = coefs_of_dot_codes[0]
        else:
            coefs = coefs_of_dot_codes[dot_codes[k]]
        fuel_consumed_for_distance = np.polyval(coefs, flight_distance)
        fuel_total_consumption_kg += fuel_consumed_for_distance
    CO2_kg = round(fuel_total_consumption_kg * 3.15)

    return CO2_kg


def plot_aircraft_codes_histogram(data_by_year):
    years_str = list(data_by_year.keys())
    dot_codes_used = []
    for yr_str in years_str:
        dot_codes_used += list(data_by_year[yr_str]['AIRCRAFT_TYPE'])

    dot_codes_used = np.array(dot_codes_used)
    dot_codes = np.unique(dot_codes_used)

    plt.title("Types of aircrafts used between 2015 and 2019")
    plt.xlabel("DOT Aircraft code")
    plt.ylabel("Number of flights done")
    plt.hist(dot_codes_used, dot_codes)
    plt.show()


# Uses average mileage for all cars classified by category (according to EPA classification). Estimates mileage from distance between cities.
# Train fuel economy on a passenger-miles per gallon basis on a national average AMTRAK load factor of 54.6%.
def other_transport(dist):
    vehicle_classes = {'Two-seater': 22, 'Subcompact': 24, 'Compact': 26, 'Midsize Sedan': 26, 'Large Sedan': 21,
                       'Hatchback': 27, 'Pickup truck': 18, 'Minivan': 20, 'Small SUV': 24, 'Standard SUV': 18}
    vehicle_classes.update({i: dist * vehicle_classes[i] for i in vehicle_classes.keys()})
    train_avg = {'train': 71.6 * dist}
    return (vehicle_classes, train_avg)