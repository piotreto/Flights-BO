from argparse import ArgumentParser
from datetime import datetime

import pickle

from flights import Reader


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('data_dir', help='path to the directory containing flights, airlines and airports csv files')
    parser.add_argument('output', help='path for the network pickled output file')
    args = parser.parse_args()

    network = Reader.read_flights(args.data_dir, datetime(2015, 5, 1), datetime(2015, 6, 30))

    with open(args.output, 'wb') as f:
        pickle.dump(network, f)
