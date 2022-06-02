from pathlib import Path
from datetime import datetime, timedelta

from flights import Reader
from flights.bees import BeeColonyAlgorithm, BeeColonyConfiguration, algorithm


# EXAMPLE APPLICATION
if __name__ == '__main__':
    start = datetime(2015, 5, 15)
    end = datetime(2015, 5, 31)

    data_dir = Path(__file__).resolve().parent.parent.parent / 'data'
    net = Reader.read_flights(data_dir, start, end)

    source = net.airports[14]
    target = net.airports[72]

    print(source.name, '->', target.name)

    # defining all the needed for an algorithm
    configuration = BeeColonyConfiguration(
        from_datetime = datetime(2015, 5, 18),
        to_datetime = datetime(2015, 5, 21, 3, 0, 0),
        max_cost = 10000,
        transfer_time = timedelta(minutes=30),
        max_transfers = 5,
        time_priority = 0.65,
        iterations = 100,
        scout_bees = 20,
        best_sites = 10,
        elite_sites = 4,
        elite_sites_bees = 4,
        rest_sites_bees = 2,
        max_shrinkages = 3
    )

    algorithm = BeeColonyAlgorithm(net, configuration)
    path = algorithm.run(source, target)

    for flight in path:
        print(flight.origin.name, '->', flight.destination.name)
        print(flight.departure, flight.arrival)
        print(flight.price)
        print()
