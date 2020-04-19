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
    This function returns a list containing statistics for different years about the number of people air traveling
    between a given origin and destination as well as the corresponding carbon emissions.
    :param past_years: List of years for which we wish to generate statistics.
    :param city_pairs: list of tuples containing two strings each representing airport codes (origin, destination).
    This list contains more than one tuple when there are several airports near the origin or the destination.
    :param data_by_year: dictionary containing yearly air trafic data produced by the select_row function.
    :param coefs_of_dot_codes: Dictionary containing the polynomial fuel consumption model of different aircrafts.
    :param number_of_years_to_predict: Integer representing the number of future years for which we wich to predict statistics.
    :param order_AR: integer representing the order of the AR model.
    :return statistics: list of dictionaries containing statistics about the number of people air traveling and the
    corresponding carbon emissions.
    """
    # 1. We first gather statistics about past years for which we have air trafic data

    statistics = [] # Initialization of the statistics

    # Past statistics corresponding to years for which we have data will be used to predict statistics for future years
    past_statistics_people = np.zeros((len(past_years)), int)
    past_statistics_CO2 = np.zeros((len(past_years)), int)

    origin = city_pairs[0][0]
    dest = city_pairs[0][1]

    for y_idx in range(len(past_years)): # For each year for which we have air trafic data
        # We add this year to the final statistics
        statistics.append({
            "year": int(past_years[y_idx]),
            "number_of_people": 0,
            "carbon_emission": 0,
            "prediction": False})
        # a. We count the number of people which traveled by plane between this origin and this destination
        number_of_people_air_travelling = count_people_air_travelling(data_by_year, origin, dest,
                                                                      int(past_years[y_idx]))
        # We keep track of this statistic to later compute predictions
        past_statistics_people[y_idx] += number_of_people_air_travelling

        statistics[y_idx]["number_of_people"] += int(number_of_people_air_travelling)

        # If we have data about people air traveling between this origin and this destination during this year
        if number_of_people_air_travelling != 0:
            # b. We compute the CO2 emissions corresponding to the total CO2 emissions produced by aircrafts which
            # flew between this origin and this destination during this year
            CO2_emissions = compute_CO2_emissions(origin, dest, int(past_years[y_idx]), data_by_year,
                                                  coefs_of_dot_codes)
            past_statistics_CO2[y_idx] += CO2_emissions # We keep track of this statistic to later compute predictions
            statistics[y_idx]["carbon_emission"] += int(CO2_emissions)

    # 2. We then predict statistics for the coming years for which we wish to predict statistics

    # Prediction of the number of people air traveling between this origin and this destination for future years
    next_statistics_people = full_prediction_AR(past_statistics_people, order_AR, number_of_years_to_predict)
    # Prediction of the carbon emissions due to air travel between this origin and this destination for future years
    next_statistics_CO2 = full_prediction_AR(past_statistics_CO2, order_AR, number_of_years_to_predict)

    # We add the predicted years to the final statistics
    for y_idx in range(number_of_years_to_predict):
        statistics.append({
            "year": int(past_years[-1]) + y_idx + 1,
            "number_of_people": int(next_statistics_people[y_idx]),  # Prediction of the number of people
            "carbon_emission": int(next_statistics_CO2[y_idx]), # Prediction of the carbon emission
            "prediction": True})  # This year corresponds to a year for which we predict data
    return statistics


def generate_all_possible_data(data_by_year, coefs_of_dot_codes, number_of_years_to_predict=5, order_AR=4):
    """
    This function returns a dictionary containing air trafic statistics for every possible city pair (origin, destination)
    :param data_by_year: dictionary containing yearly air trafic data produced by the select_row function.
    :param coefs_of_dot_codes: Dictionary containing the polynomial fuel consumption model of different aircrafts.
    :param number_of_years_to_predict: integer representing the number of future years for which we wich to predict statistics.
    :param order_AR: integer representing the order of the AR model.
    :return final_dict: dictionary containing air trafic statistics for every possible city pair (origin, destination)
    """
    past_years = list(data_by_year.keys()) # We get a list of the years for which we have air trafic data

    final_dict = {} # Initialization of the final dictionary

    # We gather all the possible origin and destination airports present in the dataset data_by_year
    possible_origins = []
    possible_destinations = []
    for year_str in past_years:
        possible_origins += list(data_by_year[year_str]['ORIGIN'])
        possible_destinations += list(data_by_year[year_str]['DEST'])
    # We make sure each origin and each destination are only present once
    possible_origins = np.unique(possible_origins)
    possible_destinations = np.unique(possible_destinations)

    # We go through the different city pairs
    for k in range(len(possible_origins)):
        for m in range(len(possible_destinations)):
            city_pair = [(possible_origins[k], possible_destinations[m])]
            # For each city pair we get statistics containing for each past and future year the number of people who
            # traveled by plane between this origin and destination as well as the total CO2 emissions.
            # For past years we compute these statistics using our dataset data_by_year and for future years we predict
            # them using an auto-regressiv model.
            stats = generate_statistics(past_years, city_pair, data_by_year, coefs_of_dot_codes,
                                        number_of_years_to_predict, order_AR)
            final_dict[city_pair[0]] = stats

    return final_dict


if __name__ == "__main__":
    # This script generates a file containing air trafic statistics for every possible city pair (origin, destination)
    # present in the yearly trafic datasets.
    # This script has not been used in our project but could have be used to generate all the possible data needed to
    # display the statistics once and for all when launching the app. It could have allowed us to save some time from the
    # user's point of view since no calculation  would have been needed in real time as all the calculation would have
    # been done beforehand.

    # Clean data
    years = [2015, 2016, 2017, 2018, 2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/Yearly traffic/' + str(y) + '_data.csv', index_col=False, encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)
    dot_to_iata = pd.read_csv('Air traffic data/aircraft_code_final.csv', index_col=False, encoding='UTF-8')
    iata_to_fuel = pd.read_csv('Air traffic data/fuel_consumption.csv', index_col=False, encoding='UTF-8')
    coefs_of_dot_codes = compute_definitive_coefficients(data_by_year, dot_to_iata, iata_to_fuel)

    # Generate file with all possible statistics
    final_dict = generate_all_possible_data(data_by_year, coefs_of_dot_codes)

    with open('statistics_and_predictions.pickle', 'wb') as handle:
        pickle.dump(final_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    with open('statistics_and_predictions.pickle', 'rb') as handle:
        b = pickle.load(handle)
