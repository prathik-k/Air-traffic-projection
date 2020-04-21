import pandas as pd
import json

#This is a clean-up script (pre-processing routine) used to create a list of medium and large airports in mainland US, along with their coordinates. 

with open('airports.json',encoding='utf8') as f:
	all_airports = json.load(f)

types = []
allowable_airports = ['medium_airport','large_airport']
us_airports = [ap for ap in all_airports if ap['iso_country'] == 'US']
us_allowed = [ap for ap in us_airports if ap['type'] in allowable_airports]

us_ap = pd.DataFrame(us_allowed)
del us_ap['local_code'],us_ap['municipality'],us_ap['continent'],us_ap['elevation_ft'],us_ap['gps_code'],us_ap['iso_region'],us_ap['iso_country'],us_ap['ident']
us_ap = us_ap.dropna(axis=0,subset=['iata_code'])

new_cols = us_ap['coordinates'].str.split(',',n=1,expand=True)
us_ap['longitude'] = new_cols[0]
us_ap['latitude'] = new_cols[1]

us_ap = us_ap.drop(['coordinates'],axis=1)
us_ap.to_csv('us_airports.csv',sep=',',encoding='utf-8',index=False)

