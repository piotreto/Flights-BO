import networkx as nx
import pandas as pd
import numpy as np  


def get_price(dist):
    return np.random.normal(0.20, 0.07) * dist

def add_edge(graph, row):
    departure_time = {'YEAR': row['YEAR'], 'MONTH': row['MONTH'], 'DAY': row['DAY'], 'TIME': row['SCHEDULED_DEPARTURE']}
    arrival_time = {'YEAR': row['YEAR'], 'MONTH': row['MONTH'], 'DAY': row['DAY'], 'TIME': row['SCHEDULED_ARRIVAL']}
    graph.add_edge(row['ORIGIN_AIRPORT'], row['DESTINATION_AIRPORT'], departure_time=departure_time, arrival_time=arrival_time, flight_time=row['SCHEDULED_TIME'], price=row['price'])

COLS = ['YEAR', 'MONTH', 'DAY', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'SCHEDULED_DEPARTURE', 'DISTANCE', 'SCHEDULED_TIME', 'SCHEDULED_ARRIVAL']
N = 100000

flights = pd.read_csv("data/flights.csv")[COLS]
flights = flights.head(N)
flights = flights[flights['SCHEDULED_TIME'].notna()]
flights['PRICE'] = flights['DISTANCE'].apply(lambda x: get_price(x))
print(flights.head(5))



MG = nx.MultiGraph()

for idx, row in flights.iterrows():
    departure_time = {'YEAR': row['YEAR'], 'MONTH': row['MONTH'], 'DAY': row['DAY'], 'TIME': row['SCHEDULED_DEPARTURE']}
    arrival_time = {'YEAR': row['YEAR'], 'MONTH': row['MONTH'], 'DAY': row['DAY'], 'TIME': row['SCHEDULED_ARRIVAL']}
    MG.add_edge(row['ORIGIN_AIRPORT'], row['DESTINATION_AIRPORT'], departure_time=departure_time, arrival_time=arrival_time, flight_time=row['SCHEDULED_TIME'], price=row['PRICE'])


    