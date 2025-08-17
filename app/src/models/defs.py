from math import radians, sin, cos, sqrt, asin


def haversine_ref_point(row, lat, lon):
    lon1 = lon
    lat1 = lat
    lon2 = row['stop_lon']
    lat2 = row['stop_lat']
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km


def get_stop_destinazione(lat, lon, stops_df):
    stop_destinazione = stops_df[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()

    # calcolo la distanza tra dove voglio andare e le fermate, cerco quella più vicina
    stop_destinazione["distance"] = stop_destinazione.apply(lambda row: haversine_ref_point(row, lat, lon), axis=1)
    stop_destinazione = stop_destinazione[stop_destinazione["distance"] == stop_destinazione["distance"].min()]
    return stop_destinazione.iloc[0]