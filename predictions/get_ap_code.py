import pandas as pd 
import numpy as np


def get_ap_codes(lat_lng_or,lat_lng_dest):
	all_airports = pd.read_csv("../Air traffic data/us_airports.csv")
	print(list(all_airports))
	lat_or,lng_or = lat_lng_or
	lat_dest,lng_dest = lat_lng_dest


	orig_data = all_airports['iata_code'][(abs(all_airports['latitude']-lat_or)<0.4) & (abs(all_airports['longitude']-lng_or)<0.4)].values
	dest_data = all_airports['iata_code'][(abs(all_airports['latitude']-lat_dest)<0.4) & (abs(all_airports['longitude']-lng_dest)<0.4)].values

	city_pairs = []
	for orig in orig_data:
		for dest in dest_data:
			citypair = (orig,dest)
			city_pairs.append(citypair)

	return city_pairs