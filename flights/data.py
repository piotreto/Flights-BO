from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from copy import copy

import networkx as nx
import numpy as np


class Airport:
    def __init__(
        self, 
        codename: str,
        name: str,
        city: str,
        state: str,
        country: str,
        longitude: float,
        latitude: float,
        terminals: int = None,
        default_transfer_time: int = timedelta(minutes=15)  # FIXME declaration is int, but default value is timedelta
    ) -> None:

        self._codename = codename
        self._name = name
    
        self._city = city
        self._state = state
        self._country = country

        self._longitude = longitude
        self._latitude = latitude

        # TODO eventually we can add proximate cities (the ones which are close enough to the airport to neglect the cost and time)

        self._terminals = terminals
        if terminals is not None:
            self._transfer_time = timedelta(minutes=15)  # TODO somehow calculate transfer time
        else:
            self._transfer_time = default_transfer_time

    @property
    def codename(self) -> str:
        return self._codename

    @property
    def name(self) -> str:
        return self._name

    @property
    def city(self) -> str:
        return self._city

    @property
    def state(self) -> str:
        return self._state

    @property
    def country(self) -> str:
        return self._country

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def terminals(self) -> Optional[int]:
        return self._terminals

    @property
    def transfer_time(self) -> timedelta:
        return self._transfer_time

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Airport):
            return False
        return self.codename == __o.codename

    def __hash__(self) -> int:
        return hash(self._codename)


class Airline:
    def __init__(self, codename: str, name: str) -> None:
        self._codename = codename
        self._name = name

    @property
    def codename(self) -> str:
        return self._codename

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Airline):
            return False
        return self._codename == __o.codename

    def __hash__(self) -> int:
        return hash(self._codename)


class Flight:
    def __init__(
        self,
        origin: Airport,
        destination: Airport,
        airline: Airline,
        departure: datetime,
        arrival: datetime,
        price: float,
        miles: int = None,
    ) -> None:
        
        self._origin: Airport = origin
        self._destination: Airport = destination

        self._airline = airline

        if departure > arrival:
            raise ValueError('departure cannot happen after the arrival')

        self._departure: datetime = departure
        self._arrival: datetime = arrival
        
        self._price: float = price

        self._miles: int = miles

    @property
    def origin(self) -> Airport:
        return self._origin

    @property
    def destination(self) -> Airport:
        return self._destination

    @property
    def airline(self) -> Airline:
        return self._airline

    @property
    def departure(self) -> datetime:
        return self._departure

    @property
    def arrival(self) -> datetime:
        return self._arrival

    @property
    def time(self) -> timedelta:
        return self._arrival - self._departure

    @property
    def price(self) -> float:
        return self._price

    @property
    def miles(self) -> int:
        return self._miles

    @property
    def kilometers(self) -> int:
        return int(self._miles * 1.60934)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Flight):
            return False
            
        return self.origin      == __o.origin \
           and self.destination == __o.destination \
           and self.airline    == __o.airline \
           and self.departure   == __o.departure \
           and self.arrival     == __o.arrival \
           and self.price       == __o.price


class Network:
    def __init__(
        self,
        airlines: List[Airline],
        airports: List[Airport],
        flights: List[Flight]
    ) -> None:

        self._airlines = airlines
        self._airports = airports
        self._flights = flights

        self._graph = nx.MultiDiGraph()

        self._graph.add_nodes_from(self._airports)
        self._graph.add_edges_from([
            (flight.origin, flight.destination, {'obj': flight})
            for flight in self._flights
        ])

        self.ant_graph = nx.MultiGraph()
        self._prepare_ant_graph()

    @property
    def airports(self) -> List[Airport]:
        return copy(self._airports)

    @property
    def flights(self) -> List[Flight]:
        return copy(self._flights)

    @property
    def airlines(self) -> List[Airline]:
        return copy(self._airlines)

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph

    def filter_by_date(self, from_date: datetime, to_date: datetime) -> Network:
        flights = [
            flight
            for flight in self._flights
            if from_date <= flight.departure and flight.arrival <= to_date
        ]

        return Network(self._airlines, self._airports, flights)

    def random_dfs_search(self, source: Airport, target: Airport, time_offset: datetime = None) -> Optional[List[Flight]]:

        if source == target:
            return []

        if time_offset is None:
            time_offset = datetime(1970, 1, 1)

        # default value is 9999th year, so that each entrance will have a better time
        visited: Dict[Airport, datetime] = defaultdict(lambda: datetime(9999, 12, 31))
        parent: Dict[Airport, Flight] = dict()
        stack = [(source, time_offset)]

        def aggregate_path():
            if target not in parent:
                return None

            path = []
            current = target
            while current != source:
                flight = parent[current]

                path.append(flight)
                current = flight.origin

            return path[::-1]

        while stack:

            airport, offset = stack.pop()
            offset += airport.transfer_time

            for u, v, k in np.random.permutation(list(self._graph.out_edges(airport, keys=True))):
                flight: Flight = self._graph.edges[u, v, k]['obj']

                if flight.departure < offset:
                    continue

                if visited[v] <= flight.arrival:
                    continue

                visited[v] = flight.arrival
                parent[v] = flight
                stack.append((v, flight.arrival))

                if v == target:
                    return aggregate_path()

        return None

    def _prepare_ant_graph(self):
        for flight in self.flights:
            self.ant_graph.add_edge(flight.origin, flight.destination, origin=flight.origin,
                                    destination=flight.destination, departure_time=flight.departure,
                                    arrival_time=flight.arrival, flight_time=flight.time, price=flight.price,
                                    pheromone_level=0, pheromone_update_time=0, flight=flight)
