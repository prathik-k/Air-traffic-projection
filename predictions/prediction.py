import pandas as pd
import numpy as np
import argparse

if __name__ != "__main__":
    from predictions.AR import full_prediction_AR
    from predictions.fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients
else:
    from AR import full_prediction_AR
    from fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients


def init_app(app):
    years = [2015, 2016, 2017, 2018, 2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/Yearly traffic/' + str(y) + '_data.csv', index_col=False, encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)

    app.data_by_year = data_by_year
    app.all_airports = pd.read_csv("Air traffic data/us_airports.csv")
    app.dot_to_iata = pd.read_csv('Air traffic data/aircraft_code_final.csv', index_col=False, encoding='UTF-8')
    app.iata_to_fuel = pd.read_csv('Air traffic data/fuel_consumption.csv', index_col=False, encoding='UTF-8')
    app.coefs_of_dot_codes = compute_definitive_coefficients(app.data_by_year, app.dot_to_iata, app.iata_to_fuel)

    return app


def select_rows(df):
    df_trimmed = df.loc[df['PASSENGERS'] != 0.0]
    df_trimmed = df_trimmed.loc[df_trimmed['SEATS'] >= 100]
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_CONFIG'].isin([1, 3])]
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_GROUP'].isin([4, 6, 7, 8])]
    df_trimmed.dropna(axis=0, inplace=True)
    return df_trimmed


def count_people_air_travelling(data_by_year, origin, dest, year):
    """
    This function returns the number of people which have been travelling by plane between an origin and a destination during a particular year.
    :param data_by_year: dictionary produced by select_row containing air data.
    :param origin: string representing the three letter code in capital letter of the origin airport.
    :param dest: string representing the three letter code in capital letter of the destination airport.
    :param year: integer representing the year.
    :return number_of_people: integer representing the number of people which travelled by plane between an origin and a destination during a particular year.
    """
    number_of_people = int(np.sum(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['PASSENGERS']))

    return number_of_people


def generate_statistics_for_request(city_pairs, data_by_year, coefs_of_dot_codes, number_of_years_to_predict=6,
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
    past_years = list(data_by_year.keys())
    past_statistics_people = np.zeros((len(past_years)), int)
    past_statistics_CO2 = np.zeros((len(past_years)), int)

    for y_idx in range(len(past_years)):
        statistics.append({
            "year": int(past_years[y_idx]),
            "number_of_people": 0,
            "carbon_emission": 0,
            "prediction": False})
        for origin, dest in city_pairs:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Predicts number of people travelling by flight between an origin and a destination. The prediction model used is an auto-regressive model.")

    parser.add_argument("origin", type=str, help="The three letter code of the origin airport. Ex: 'JFK'.")
    parser.add_argument("dest", type=str, help="The three letter code of the destination airport. Ex: 'BOS'.")
    parser.add_argument("order_AR", type=int, help="The order of the auto-regressive model. Ex: 3.")
    parser.add_argument("number_of_years_to_predict", type=int, help="The number of future years to predict. Ex: 5.")

    args = parser.parse_args()

    # Clean data
    years = [2015, 2016, 2017, 2018, 2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/Yearly traffic/' + str(y) + '_data.csv', index_col=False, encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)
    dot_to_iata = pd.read_csv('Air traffic data/aircraft_code_final.csv', index_col=False, encoding='UTF-8')
    iata_to_fuel = pd.read_csv('Air traffic data/fuel_consumption.csv', index_col=False, encoding='UTF-8')

    # Get the number of people that travelled by flight between NY and Boston for each year between year 2015 and year 2019
    past_years = list(data_by_year.keys())
    past_statistics = np.zeros((len(past_years)), int)
    for y_idx in range(len(past_years)):
        past_statistics[y_idx] = count_people_air_travelling(data_by_year, args.origin, args.dest,
                                                             int(past_years[y_idx]))

    print('Number of people air travelling from {} to {} for years {} to {}: {}'.format(args.origin, args.dest,
                                                                                        int(past_years[0]),
                                                                                        int(past_years[-1]),
                                                                                        past_statistics))

    # Auto-regressive model to predict the number of people that will travel by flight between NY and Boston for each year between year 2020 and year 2025
    next_statistics = full_prediction_AR(past_statistics, args.order_AR, args.number_of_years_to_predict)

    print(
        'Predicted number of people air travelling from {} to {} for years {} to {}: {}'.format(args.origin, args.dest,
                                                                                                int(past_years[-1]) + 1,
                                                                                                int(past_years[
                                                                                                        -1]) + args.number_of_years_to_predict,
                                                                                                next_statistics))

    # Generate statistics in correct format for request
    city_pairs = [('ATL', 'JFK'), ('ATL', 'EWK'), ('ATL', 'LGA')]
    statistics = generate_statistics_for_request(city_pairs, data_by_year, dot_to_iata, iata_to_fuel)
    print(statistics)
