import pandas as pd
import numpy as np

if __name__ != "__main__":
    from predictions.AR import full_prediction_AR
    from predictions.fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients
else:
    from AR import full_prediction_AR
    from fuel_consumption import compute_CO2_emissions, compute_definitive_coefficients


def init_app(app):
    """
    This function loads the data needed for predictions.
    :param app: object representing the web server.
    :return app: object representing the web server initialized with the data needed to do predictions.
    """
    years = [k for k in range(2010, 2020)]

    # We gather yearly air trafic data into a dictionary called data_by_year
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/Yearly traffic/' + str(y) + '_data.csv', index_col=False,
                         encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)

    app.data_by_year = data_by_year  # Data corresponding to yearly air trafic
    # Data mapping airport names to airport three-letter codes
    app.all_airports = pd.read_csv("Air traffic data/us_airports.csv")
    # Data mapping aicraft DOT codes to aircraft IATA codes. Also provides the number of seats of each aircraft.
    app.dot_to_iata = pd.read_csv('Air traffic data/aircraft_code_final.csv', index_col=False, encoding='UTF-8')
    # Data mapping fuel consumption to aircraft IATA codes
    app.iata_to_fuel = pd.read_csv('Air traffic data/fuel_consumption.csv', index_col=False, encoding='UTF-8')
    # Parameters used to compute the fuel consumption of each aircraft
    app.coefs_of_dot_codes = compute_definitive_coefficients(app.data_by_year, app.dot_to_iata, app.iata_to_fuel)

    return app


def select_rows(df):
    """
    This function gets relevant data from data corresponding to one year of air trafic data.
    :param df: pandas.DataFrame corresponding to air trafic data of a specific year. Each row contains monthly
    statistics for specific origin, destination, aircraft type and carrier.
    :return df_trimmed: pandas.DataFrame corresponding to relevant data.
    """
    df_trimmed = df.loc[df['PASSENGERS'] != 0.0]  # We do not take into consideration flights with no passengers in it
    # We only take into consideration relatively big aircrafts, with more than 100 seats
    df_trimmed = df_trimmed.loc[df_trimmed['SEATS'] >= 100]
    # We do not keep data corresponding to seaplanes
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_CONFIG'].isin([1, 3])]
    # We do not keep data corresponding to helicopters or tourist airplanes
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_GROUP'].isin([4, 6, 7, 8])]
    df_trimmed.dropna(axis=0, inplace=True)

    return df_trimmed


def count_people_air_travelling(data_by_year, origin, dest, year):
    """
    This function returns the number of people which have been travelling by plane between an origin and a destination
    during a particular year.
    :param data_by_year: dictionary produced by select_row containing air data.
    :param origin: string representing the three letter code in capital letter of the origin airport.
    :param dest: string representing the three letter code in capital letter of the destination airport.
    :param year: integer representing the year.
    :return number_of_people: integer representing the number of people which travelled by plane between an origin and
    a destination during a particular year.
    """
    number_of_people = int(np.sum(data_by_year[str(year)].iloc[np.where(
        (data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['PASSENGERS']))

    return number_of_people


def generate_statistics_for_request(city_pairs, data_by_year, coefs_of_dot_codes, number_of_years_to_predict=6,
                                    order_AR=3):
    """
    This function returns a list containing statistics for different years about the number of people air traveling
    between a given origin and destination as well as the corresponding carbon emissions.
    :param city_pairs: list of tuples containing two strings each representing airport codes (origin, destination).
    This list contains more than one tuple when there are several airports near the origin or the destination.
    :param data_by_year: dictionary containing yearly air trafic data produced by the select_row function.
    :param number_of_years_to_predict: integer representing the number of future years for which we wich to predict statistics.
    :param order_AR: integer representing the order of the AR model.
    :return statistics: list of dictionaries containing statistics about the number of people air traveling and the
    corresponding carbon emissions.
    """

    # If we have not found the airports near the selected locations
    if len(city_pairs) == 0:
        return None

    # 1. We first gather statistics about past years for which we have air trafic data

    statistics = []  # Initialization of the statistics
    past_years = sorted(data_by_year.keys())  # These years correspond to years for which we have air trafic data

    # Past statistics corresponding to years for which we have data will be used to predict statistics for future years
    past_statistics_people = np.zeros((len(past_years)), int)
    past_statistics_CO2 = np.zeros((len(past_years)), int)

    # Check if we find interesting data during our computation
    valid_data = False

    for y_idx in range(len(past_years)):  # For each year for which we have air trafic data
        # We add this year to the final statistics
        statistics.append({
            "year": int(past_years[y_idx]),
            "number_of_people": 0,  # Initialization of the number of people
            "carbon_emission": 0,  # Initialization of the carbon emission
            "prediction": False})  # This year corresponds to a year for which we have data and not to a prediction

        for origin, dest in city_pairs:  # For each pair of origin airport and destination airport
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
                past_statistics_CO2[
                    y_idx] += CO2_emissions  # We keep track of this statistic to later compute predictions
                statistics[y_idx]["carbon_emission"] += int(CO2_emissions)

        if statistics[y_idx]["carbon_emission"] != 0 and statistics[y_idx]["number_of_people"] != 0:
            valid_data = True

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
            "carbon_emission": int(next_statistics_CO2[y_idx]),  # Prediction of the carbon emission
            "prediction": True})  # This year corresponds to a year for which we predict data

    if not valid_data:
        return None

    return statistics
