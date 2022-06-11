from argparse import ArgumentParser
from operator import attrgetter
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import sys

import streamlit as st
import pydeck as pdk
import matplotlib

from flights import Reader, Network, Flight
from flights.bees import BeeColonyAlgorithm, BeeColonyConfiguration
from flights.ants import AntColonyConfiguration, AntColonyAlgorithm


def ant_colony_algorithm(net: Network) -> Optional[List[Flight]]:
    st.sidebar.write('Algorithm hyperparameters')
    iters_numb = st.sidebar.number_input('Iterations', min_value=1, max_value=1000000000, value=1000, step=10)
    result_samples = st.sidebar.number_input('Result samples', min_value=1, max_value=1000000, value=10, step=10)
    ants_number = st.sidebar.number_input('Ants number', min_value=1, max_value=1000000, value=100, step=10)
    ants_spawn_iters = st.sidebar.number_input('Spawn iterations', min_value=1, max_value=1000, value=10, step=1)
    connection_samples = st.sidebar.number_input('Connection samples', min_value=1, max_value=1000, value=3, step=1)
    direct_connection_impact = st.sidebar.slider('Direct connection impact', min_value=0.0, max_value=1.0, value=0.8, step=0.01)
    pheromone_impact = st.sidebar.slider('Pheromone impact', min_value=0.0, max_value=1.0, value=0.4, step=0.01)
    time_impact_nodes = st.sidebar.slider('Cost impact - Time impact (in nodes)', min_value=0.0, max_value=1.0, value=0.6, step=0.01)
    pheromone_updating_time = st.sidebar.number_input('Pheromone updating time', min_value=1, max_value=1000000, value=1000, step=10)

    st.markdown('### Options')
    c1, c2 = st.columns(2)

    with c1:
        max_price = st.number_input('Max cost', min_value=1, value=10000, step=10)
        time_impact_choice = st.slider('Cost priority - Time priority (in result choice)', min_value=0.0, max_value=1.0, value=0.5, step=0.01)
        min_time = st.date_input('Journey start date', min_value=START_DATE, max_value=END_DATE, value=START_DATE)

    with c2:
        max_conn_numb = st.number_input('Max transfers', min_value=0, value=5, step=1)
        min_conn_time = st.number_input('Transfer time (minutes)', min_value=0, value=90, step=5)
        max_time = st.date_input('Journey end date', min_value=START_DATE, max_value=END_DATE, value=END_DATE)

    st.markdown('### Airports')
    airports = sorted(net.airports, key=attrgetter('city'))
    options = list(range(len(airports)))
    c1, c2 = st.columns(2)

    with c1:
        origin_idx = st.selectbox('Origin', options=options,
                                  format_func=lambda i: f'{airports[i].city}, {airports[i].state} ({airports[i].name})')
        origin = airports[origin_idx]

    with c2:
        destination_idx = st.selectbox('Destination', options=options, format_func=lambda
            i: f'{airports[i].city}, {airports[i].state} ({airports[i].name})')
        destination = airports[destination_idx]

    # parameters verification block
    verified = True
    if ants_spawn_iters > ants_number:
        st.warning('Number of spawn iterations cannot be higher than ants number')
        verified = False
    if ants_number > 3 * iters_numb:
        st.warning('Number of iterations must be at least 3 times higher than ants number')
        verified = False
    if min_time >= max_time:
        st.warning('End date must be later than the start date')
        verified = False
    if origin == destination:
        st.warning('Origin and destination airports must be different')
        verified = False

    if st.button('Find'):
        if not verified:
            st.error('You cannot run the algorithm while there are warnings about the parameters')
            return None

        configuration = AntColonyConfiguration(
            iters_numb = iters_numb,
            result_samples = result_samples,
            ants_number = ants_number,
            ants_spawn_iters = ants_spawn_iters,
            connection_samples = connection_samples,
            direct_connection_impact = direct_connection_impact,
            time_impact_nodes = time_impact_nodes,
            pheromone_impact = pheromone_impact,
            pheromone_updating_time = pheromone_updating_time,
            min_time = datetime(min_time.year, min_time.month, min_time.day),
            max_time = datetime(max_time.year, max_time.month, max_time.day),
            min_conn_time = min_conn_time,
            max_conn_numb = max_conn_numb,
            max_price = max_price,
            time_impact_choice = time_impact_choice
        )

        try:
            algorithm = AntColonyAlgorithm(net, configuration)
            return algorithm.run(origin, destination)
        except Exception as ex:
            print(ex.with_traceback())
            st.error(str(ex))

    return None


def bee_colony_algorithm(net: Network) -> Optional[List[Flight]]:
    st.sidebar.write('Algorithm hyperparameters')
    iterations       = st.sidebar.number_input('Iterations', min_value=1, max_value=1000, value=100, step=5)
    scout_bees       = st.sidebar.number_input('Scout bees', min_value=1, max_value=100, value=20, step=1)
    best_sites       = st.sidebar.number_input('Best sites', min_value=2, max_value=50, value=10, step=1)
    elite_sites      = st.sidebar.number_input('Elite sites', min_value=1, max_value=30, value=4, step=1)
    elite_sites_bees = st.sidebar.number_input('Bees recruited for elite sites', min_value=1, max_value=20, value=4, step=1)
    rest_sites_bees  = st.sidebar.number_input('Beest recruited for the rest of the sites', min_value=1, max_value=20, value=2, step=1)
    max_shrinkages   = st.sidebar.number_input('Max shrinkages', min_value=1, max_value=10, value=3, step=1)

    st.markdown('### Options')
    c1, c2 = st.columns(2)

    with c1:
        max_cost      = st.number_input('Max cost', min_value=1, value=10000, step=10)
        time_priority = st.slider('Cost priority - Time priority', min_value=0.0, max_value=1.0, value=0.5, step=0.01)
        from_date     = st.date_input('Journey start date', min_value=net.start_date, max_value=net.end_date, value=net.start_date)

    with c2:
        max_transfers = st.number_input('Max transfers', min_value=0, value=5, step=1)
        transfer_time = st.number_input('Transfer time (minutes)', min_value=0, value=30, step=5)
        to_date       = st.date_input('Journey end date', min_value=net.start_date, max_value=net.end_date, value=net.end_date)

    st.markdown('### Airports')
    airports = sorted(net.airports, key=attrgetter('city'))
    options = list(range(len(airports)))
    c1, c2 = st.columns(2)

    with c1:
        origin_idx = st.selectbox('Origin', options=options, format_func=lambda i: f'{airports[i].city}, {airports[i].state} ({airports[i].name})')
        origin = airports[origin_idx]

    with c2:
        destination_idx = st.selectbox('Destination', options=options, format_func=lambda i: f'{airports[i].city}, {airports[i].state} ({airports[i].name})')
        destination = airports[destination_idx]

    # parameters verification block
    verified = True
    if best_sites > scout_bees:
        st.warning('There can be no more best sites than scout bees')
        verified = False
    if elite_sites > best_sites:
        st.warning('There can be no more elite sites than best sites')
        verified = False
    if from_date >= to_date:
        st.warning('End date must be later than the start date')
        verified = False
    if origin == destination:
        st.warning('Origin and destination airports must be different')
        verified = False

    if st.button('Find'):

        if not verified:
            st.error('You cannot run the algorithm while there are warnings about the parameters')
            return None
        
        configuration = BeeColonyConfiguration(
            from_datetime = datetime(from_date.year, from_date.month, from_date.day),
            to_datetime = datetime(to_date.year, to_date.month, to_date.day),
            max_cost = max_cost,
            transfer_time = timedelta(minutes=transfer_time),
            max_transfers = max_transfers,
            time_priority = time_priority,
            iterations = iterations,
            scout_bees = scout_bees,
            best_sites = best_sites,
            elite_sites = elite_sites,
            elite_sites_bees = elite_sites_bees,
            rest_sites_bees = rest_sites_bees,
            max_shrinkages = max_shrinkages
        )

        algorithm = BeeColonyAlgorithm(net, configuration)
        return algorithm.run(origin, destination)

    return None


def main(net: Network):
    st.title('Flightify')

    st.sidebar.write('Algorithm')
    algorithm_name = st.sidebar.selectbox(
        'Select algorithm',
        options=[
            'Ant Colony Algorithm',
            'Bee Colony Algorithm'
        ]
    )

    if algorithm_name == 'Ant Colony Algorithm':
        path = ant_colony_algorithm(net)
    elif algorithm_name == 'Bee Colony Algorithm':
        path = bee_colony_algorithm(net)
    else:
        st.error('Unkown algorithm')

    st.markdown('---')

    if path is not None:
        st.markdown('### Route')
        total_price = sum(flight.price for flight in path)
        total_time = (path[-1].arrival - path[0].departure).total_seconds() // 60

        st.write(f'Total price: {total_price:.2f}$')
        st.write(f'Total time: {total_time // 60} hours, {total_time % 60} minutes')
        st.write('')

        for flight in path:
            st.write(f'{flight.origin.city}, {flight.origin.state} ({flight.origin.name})  ---> {flight.destination.city}, {flight.destination.state} ({flight.destination.name})')
            st.write(f'{flight.departure} - {flight.arrival}')
            st.write(f'{flight.price:.2f}$, {flight.airline.name}')
            st.write('')

        # drawing a map
        cmap = matplotlib.cm.get_cmap('cubehelix')

        data = [{
            'name': f'{flight.origin.city} -> {flight.destination.city}',
            'color': tuple(map(lambda x: 255 * x, cmap((i + 1) / (len(path) + 1))[:3])),
            'path': [
                [flight.origin.longitude, flight.origin.latitude],
                [flight.destination.longitude, flight.destination.latitude]
            ]
        } for i, flight in enumerate(path)]

        longitude = sum([flight.origin.longitude for flight in path] + [path[-1].destination.longitude]) / (len(path) + 1)
        latitude = sum([flight.origin.latitude for flight in path] + [path[-1].destination.latitude]) / (len(path) + 1)

        view_state = pdk.ViewState(
            longitude=longitude,
            latitude=latitude,
            zoom=5
        )

        layer = pdk.Layer(
            type='PathLayer',
            data=data,
            pickable=True,
            get_color='color',
            width_scale=20,
            width_min_pixels=2,
            get_path='path',
            get_width=5
        )

        deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={'text': '{name}'})

        st.pydeck_chart(deck)

    else:
        st.error('Have not found any possible flights')
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('pickled_network', help='path to the pickled Network object')
    args = parser.parse_args(sys.argv[1:])

    if 'net' not in st.session_state:
        net = Reader.read_network_pickled(args.pickled_network)
        st.session_state.net = net

    main(st.session_state.net)
