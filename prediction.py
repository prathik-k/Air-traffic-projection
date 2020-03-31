import pandas as pd
import numpy as np

def select_rows(df):
    df_trimmed = df.loc[df['PASSENGERS'] != 0.0]
    df_trimmed = df_trimmed.loc[df_trimmed['SEATS'] >= 100]
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_CONFIG'].isin([1,3])]
    df_trimmed = df_trimmed.loc[df_trimmed['AIRCRAFT_GROUP'].isin([4,6,7,8])]
    df_trimmed.dropna(axis=0,inplace=True)
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
    number_of_people = np.int(np.sum(data_by_year[str(year)].iloc[np.where((data_by_year[str(year)]['ORIGIN'] == origin) & (data_by_year[str(year)]['DEST'] == dest))]['PASSENGERS']))

    return number_of_people

if __name__ == "__main__":
    years = [2015,2016,2017,2018,2019]
    data_by_year = {}
    for y in years:
        df = pd.read_csv('Air traffic data/'+str(y)+'_data.csv', index_col=False,encoding = 'UTF-8').drop(['Unnamed: 14'],axis=1)
        data_by_year[str(y)] = select_rows(df)

    print(count_people_air_travelling(data_by_year, 'JFK', 'BOS', 2015))