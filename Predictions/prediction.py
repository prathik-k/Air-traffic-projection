import pandas as pd
import numpy as np
from Predictions.AR import create_matrices_used_to_compute_parameters, compute_parameters, create_matrix_for_prediction, predict_next_statistics


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


if __name__ == "__main__":

    # Clean data
    years = [2015, 2016, 2017, 2018, 2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/' + str(y) + '_data.csv', index_col=False, encoding='UTF-8').drop(
            ['Unnamed: 14'], axis=1)
        data_by_year[str(y)] = select_rows(df)

    # Get the number of people that travelled by flight between NY and Boston for the different years
    origin = 'JFK'
    dest = 'BOS'

    past_statistics = np.zeros((len(years)), int)
    for y_idx in range(len(years)):
        past_statistics[y_idx] = count_people_air_travelling(data_by_year, origin, dest, years[y_idx])

    # Auto-regressive model to predict the number of people that will travel by flight between NY and Boston for the years to come
    order_AR = 3

    A, b = create_matrices_used_to_compute_parameters(past_statistics, order_AR)
    parameters = compute_parameters(A, b)

    number_of_years_to_predict = 5
    A_prediction = create_matrix_for_prediction(past_statistics, order_AR, number_of_years_to_predict)

    next_statistics = predict_next_statistics(A_prediction, parameters, order_AR)

    print(next_statistics)


