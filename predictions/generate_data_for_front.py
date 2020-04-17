import numpy as np
import pandas as pd
import pickle

if __name__ != "__main__":
    from predictions.prediction import count_people_air_travelling, select_rows
    from predictions.AR import full_prediction_AR
    from predictions.fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients
else:
    from prediction import count_people_air_travelling, select_rows
    from AR import full_prediction_AR
    from fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients


def generate_statistics(past_years, city_pairs, data_by_year, coefs_of_dot_codes, number_of_years_to_predict=3,
                        order_AR=4):
    """
    This function returns a list containing statistics.
    :param city_pairs: list of tuples containing two strings each representing airport codes (origin, destination)
    :param data_by_year: dictionary produced by select_row containing air data.
    :param number_of_years_to_predict: integer representing the number of future years for which we wich to predict statistics.
    :param order_AR: integer representing the order of the AR model.
    :return statistics: list of dictionaries containing the statistics.
    """
    statistics = []
    past_statistics_people = np.zeros((len(past_years)), int)
    past_statistics_CO2 = np.zeros((len(past_years)), int)

    origin = city_pairs[0][0]
    dest = city_pairs[0][1]

    for y_idx in range(len(past_years)):
        statistics.append({
            "year": int(past_years[y_idx]),
            "number_of_people": 0,
            "carbon_emission": 0,
            "prediction": False})

        number_of_people_air_travelling = count_people_air_travelling(data_by_year, origin, dest,
                                                                      int(past_years[y_idx]))
        past_statistics_people[y_idx] += number_of_people_air_travelling
        statistics[y_idx]["number_of_people"] += int(number_of_people_air_travelling)
        if number_of_people_air_travelling != 0:
            CO2_emissions = compute_CO2_emissions(origin, dest, int(past_years[y_idx]), data_by_year,
                                                  coefs_of_dot_codes)
            past_statistics_CO2[y_idx] += CO2_emissions
            statistics[y_idx]["carbon_emission"] += int(CO2_emissions)
    next_statistics_people = full_prediction_AR(past_statistics_people, order_AR, number_of_years_to_predict)
    next_statistics_CO2 = full_prediction_AR(past_statistics_CO2, order_AR, number_of_years_to_predict)
    for y_idx in range(number_of_years_to_predict):
        statistics.append({
            "year": int(past_years[-1]) + y_idx + 1,
            "number_of_people": int(next_statistics_people[y_idx]),
            "carbon_emission": int(next_statistics_CO2[y_idx]),
            "prediction": True})
    return statistics


def generate_all_possible_data(data_by_year, coefs_of_dot_codes, number_of_years_to_predict=5, order_AR=4):

    past_years = list(data_by_year.keys())
    final_dict = {}
    possible_origins = []
    possible_destinations = []
    for year_str in past_years:
        possible_origins += list(data_by_year[year_str]['ORIGIN'])
        possible_destinations += list(data_by_year[year_str]['DEST'])
    possible_origins = np.unique(possible_origins)
    possible_destinations = np.unique(possible_destinations)
    for k in range(len(possible_origins)):
        print("origin number: " + str(k))
        for m in range(len(possible_destinations)):
            city_pair = [(possible_origins[k], possible_destinations[m])]
            stats = generate_statistics(past_years, city_pair, data_by_year, coefs_of_dot_codes,
                                        number_of_years_to_predict, order_AR)
            final_dict[city_pair[0]] = stats
    return final_dict


if __name__ == "__main__":
    # Clean data
    years = [2015, 2016, 2017, 2018, 2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/' + str(y) + '_data.csv', index_col=False, encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)
    dot_to_iata = pd.read_csv('Air traffic data/aircraft_code_final.csv', index_col=False, encoding='UTF-8')
    iata_to_fuel = pd.read_csv('Air traffic data/fuel_consumption.csv', index_col=False, encoding='UTF-8')
    coefs_of_dot_codes = compute_definitive_coefficients(data_by_year, dot_to_iata, iata_to_fuel)

    # Generate file with everything
    final_dict = generate_all_possible_data(data_by_year, coefs_of_dot_codes)

    with open('statistics_and_predictions.pickle', 'wb') as handle:
        pickle.dump(final_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('statistics_and_predictions.pickle', 'rb') as handle:
        b = pickle.load(handle)
