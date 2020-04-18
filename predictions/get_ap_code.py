import pandas as pd

def get_ap_codes(all_airports, lat_lng_or, lat_lng_dest):
	"""
	This function accepts the latitude and longitude of the origin destination pairs, and returns all airports in close proximity to the coordinates. 
	E.g. using (40.713,-74.006) for either coordinate returns "LGA","EWR","ISP" and "JFK" - the airports serving NYC.
	:param all_airports: List of all airports in mainland US along with coordinates
	:param lat_lng_or: latitude & longitude of origin as tuple
	:param lat_lng_dest: latitude & longitude of destination as tuple
	:return city_pairs: list of tuples of (origin,destination)
	"""
        lat_or,lng_or = lat_lng_or
        lat_dest,lng_dest = lat_lng_dest

        orig_data = all_airports['iata_code'][(abs(all_airports['latitude'] - lat_or) < 0.4) & (abs(all_airports['longitude'] - lng_or) < 0.4)].values
        dest_data = all_airports['iata_code'][(abs(all_airports['latitude'] - lat_dest) < 0.4) & (abs(all_airports['longitude'] - lng_dest) < 0.4)].values

        city_pairs = []
        for orig in orig_data:
                for dest in dest_data:
                        citypair = (orig,dest)
                        city_pairs.append(citypair)

        return city_pairs
