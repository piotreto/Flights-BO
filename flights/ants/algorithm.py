import random
import queue
import numpy as np
import datetime

from .configuration import AntColonyConfiguration
from ..data import Network, Flight, Airport


class Ant:
    def __init__(self, curr_time, curr_airport):
        self.curr_time = curr_time
        self.curr_airport = curr_airport
        self.mode = 'NORMAL'

        self.curr_trav_cost = 0
        self.curr_conn_numb = 0
        self.path = []

    def __lt__(self, other):
        if self.mode != other.mode:
            return self.mode < other.mode
        return self.curr_time < other.curr_time

    def __gt__(self, other):
        if self.mode != other.mode:
            return self.mode > other.mode
        return self.curr_time > other.curr_time

    def __eq__(self, other):
        return self.mode == other.mode and self.curr_time == other.curr_time

    def __ne__(self, other):
        return not self.__eq__(other)

    def update(self, flight):
        self.curr_time = flight[2]['arrival_time']
        self.curr_airport = flight[0]
        self.curr_trav_cost += flight[2]['price']
        self.curr_conn_numb += 1
        self.path.append(flight[2]['flight'])


class AntColonyAlgorithm:
    def __init__(self, network: Network, configuration: AntColonyConfiguration):
        self.net = network
        self.config = configuration

        self.global_time = 0
        self.events = queue.PriorityQueue()

    def clean_pheromones(self, mg):
        for airport_1 in mg.nodes:
            for airport_2 in mg.adj[airport_1]:
                for flight in mg.adj[airport_1][airport_2]:
                    mg.adj[airport_1][airport_2][flight]['pheromone_level'] = 0
                    mg.adj[airport_1][airport_2][flight]['pheromone_update_time'] = 0

    ###
    def _init_ants(self, origin):
        time_available_min = (self.config.max_time - self.config.min_time).total_seconds() // 60

        ants_spawn_gap = time_available_min // self.config.ants_spawn_iters
        for i in range(self.config.ants_spawn_iters):
            for j in range(self.config.ants_number // self.config.ants_spawn_iters):
                self.events.put((i * ants_spawn_gap,
                                 Ant(self.config.min_time + datetime.timedelta(minutes=i * ants_spawn_gap), origin)))

    ###
    def _run_next_event(self, origin, destination, get_results=False, results=None):
        self.global_time, curr_ant = self.events.get()
        available_flights = self._find_available_flights(curr_ant)
        self._update_pheromones(available_flights)
        next_flight = self._choose_flight(available_flights, curr_ant, origin, destination)
        self._make_next_flight(next_flight, curr_ant, get_results, results, origin, destination)

    ###
    def _find_available_flights(self, curr_ant):
        all_flights = self.net.ant_graph[curr_ant.curr_airport]
        available_flights = []

        for airport in all_flights:
            flights_added = 0
            if curr_ant.mode == 'NORMAL':
                start, end, order = 0, len(self.net.ant_graph.adj[curr_ant.curr_airport][airport]), 1
            else:  # curr_ant.mode == 'RETURN'
                start, end, order = len(self.net.ant_graph.adj[curr_ant.curr_airport][airport]) - 1, -1, -1

            for flight_idx in range(start, end, order):
                flight = self.net.ant_graph.adj[curr_ant.curr_airport][airport][flight_idx]
                if self._is_accessible_flight(curr_ant, flight):
                    available_flights.append((airport, flight_idx, flight))
                    flights_added += 1
                    if flights_added == self.config.connection_samples:
                        break

        return available_flights

    def _is_accessible_flight(self, curr_ant, flight):
        if curr_ant.mode == 'NORMAL':
            good_airport = curr_ant.curr_airport == flight['origin']
            good_departure = curr_ant.curr_time + datetime.timedelta(minutes=self.config.min_conn_time) <= flight[
                'departure_time']
            good_arrival = flight['arrival_time'] <= self.config.max_time
        else:  # curr_ant.mode == 'RETURN'
            good_airport = curr_ant.curr_airport == flight['destination']
            good_arrival = curr_ant.curr_time - datetime.timedelta(minutes=self.config.min_conn_time) >= flight['arrival_time']
            good_departure = flight['departure_time'] >= self.config.min_time

        good_cost = curr_ant.curr_trav_cost + flight['price'] <= self.config.max_price
        return good_airport and good_departure and good_arrival and good_cost

    ###
    def _update_pheromones(self, available_flights):
        for airport, index, flight in available_flights:
            time_gap = self.global_time - flight['pheromone_update_time']
            flight['pheromone_level'] = flight['pheromone_level'] * (0.5) ** (time_gap // self.config.pheromone_updating_time)
            flight['pheromone_update_time'] = self.global_time

    ###
    def _choose_flight(self, flights, curr_ant, origin, destination):
        if len(flights) == 0:
            return None

        for airport, index, flight in flights:
            if curr_ant.mode == 'NORMAL' and airport == destination or curr_ant.mode == 'RETURN' and airport == origin:
                if random.random() < self.config.direct_connection_impact:
                    flight['pheromone_level'] += 1
                    return airport, index, flight

        waiting_times, prices, pheromones = np.empty(len(flights)), np.empty(len(flights)), np.empty(len(flights))

        min_time = curr_ant.curr_time + datetime.timedelta(
            minutes=self.config.min_conn_time) if curr_ant.mode == 'NORMAL' else None
        max_time = curr_ant.curr_time - datetime.timedelta(
            minutes=self.config.min_conn_time) if curr_ant.mode == 'RETURN' else None

        for index, (airport, flight_index, flight) in enumerate(flights):
            if curr_ant.mode == 'NORMAL':
                waiting_times[index] = (flight['departure_time'] - min_time).total_seconds() // 60
            if curr_ant.mode == 'RETURN':
                waiting_times[index] = (max_time - flight['arrival_time']).total_seconds() // 60
            prices[index] = flight['price']
            pheromones[index] = flight['pheromone_level']

        time_coeffs = (1 - np.nan_to_num(waiting_times / np.max(waiting_times))) ** 3
        prices_coeffs = (1 - np.nan_to_num(prices / np.max(prices))) ** 3
        pheromones_coeffs = np.nan_to_num(pheromones / np.max(pheromones))

        pheromone_impact = self.config.pheromone_impact
        time_impact = self.config.time_impact_nodes * (1 - pheromone_impact)
        cost_impact = 1 - self.config.pheromone_impact - time_impact
        combined_params = time_coeffs * time_impact + prices_coeffs * cost_impact + pheromones_coeffs * pheromone_impact

        flight_pos = random.uniform(0, sum(combined_params))
        for flight, params in zip(flights, combined_params):
            if params >= flight_pos:
                flight[2]['pheromone_level'] += 1
                return flight
            flight_pos -= params

    ###
    def _make_next_flight(self, next_flight, curr_ant, get_results, results, origin, destination):
        if next_flight is None or curr_ant.curr_conn_numb == self.config.max_conn_numb:
            self._spawn_ant(origin)

        else:
            if curr_ant.mode == 'NORMAL':
                time_diff = (next_flight[2]['arrival_time'] - curr_ant.curr_time).total_seconds() // 60
            else:  # curr_ant.mode == 'RETURN'
                time_diff = (curr_ant.curr_time - next_flight[2]['departure_time']).total_seconds() // 60
            new_time = self.global_time + time_diff

            curr_ant.update(next_flight)
            if curr_ant.mode == 'NORMAL' and next_flight[0] == destination:
                if get_results:
                    results.append((curr_ant.curr_trav_cost, curr_ant.curr_conn_numb, curr_ant.path))
                    self._spawn_ant(origin)
                else:
                    curr_ant.curr_trav_cost = 0
                    curr_ant.curr_conn_numb = 0
                    curr_ant.mode = 'RETURN'
                    self.events.put((new_time, curr_ant))
            elif curr_ant.mode == 'RETURN' and next_flight[0] == origin:
                self._spawn_ant(origin)
            else:
                self.events.put((new_time, curr_ant))

    def _spawn_ant(self, origin):
        time_available_min = int((self.config.max_time - self.config.min_time).total_seconds() // 60)
        ant_spawn_gap = random.randint(0, time_available_min)
        self.events.put(
            (self.global_time + 1, Ant(self.config.min_time + datetime.timedelta(minutes=ant_spawn_gap), origin)))

    ###
    def _find_best_result(self, results):
        costs, total_times = np.empty(len(results)), np.empty(len(results))

        for index, result in enumerate(results):
            costs[index] = result[0]
            total_times[index] = (result[2][-1].arrival - result[2][0].departure).total_seconds() // 60

        costs = np.nan_to_num(costs / np.max(costs))
        total_times = np.nan_to_num(total_times / np.max(total_times))
        full_params = total_times * self.config.time_impact_choice + costs * (1 - self.config.time_impact_choice)

        results_params = [(result, params) for result, params in zip(results, full_params)]
        results_params.sort(key=lambda x: x[1])
        return results_params[0][0][2]

    ###
    def run(self, origin: Airport, destination: Airport):
        self.clean_pheromones(self.net.ant_graph)

        self._init_ants(origin)

        counter = 0
        while counter < self.config.iters_numb:
            self._run_next_event(origin, destination)
            counter += 1

        results = []
        while len(results) < self.config.result_samples:
            self._run_next_event(origin, destination, True, results)
        return self._find_best_result(results)
