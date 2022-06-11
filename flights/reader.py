from datetime import datetime, date, time, timedelta
from typing import Dict, Optional
from pathlib import Path

import scipy.stats as st
import pandas as pd
import numpy as np
import pickle

from .data import Network, Airline, Airport, Flight


class Reader:
    FLIGHTS_COLS = ['YEAR', 'MONTH', 'DAY', 'AIRLINE', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'SCHEDULED_DEPARTURE', 'DISTANCE', 'SCHEDULED_TIME', 'SCHEDULED_ARRIVAL']

    @staticmethod
    def random_price(size: int):
        lowcost_count = int((1 / 11.7) * size)
        normalcost_count = int((10 / 11.7) * size)
        highcost_count = size - lowcost_count - normalcost_count

        values = np.concatenate([
            st.norm.ppf(np.random.random(size=lowcost_count),    loc=0.1, scale=0.04),
            st.norm.ppf(np.random.random(size=normalcost_count), loc=0.3, scale=0.15),
            st.norm.ppf(np.random.random(size=highcost_count),   loc=0.8, scale=0.1)
        ])

        return np.maximum(0, values)

    @staticmethod
    def _generate_price(dists: np.ndarray):
        return np.maximum(
            0,
            np.round(
                Reader.random_price(dists.shape[0]) * dists + np.random.normal(30, 15, size=dists.shape[0]),
                2
            )
        )

    # TODO would be great to get the real numbers of terminals
    # I searched for 15 minutes and couldn't find anything related, should check better resources
    @staticmethod
    def _generate_terminals(size: int) -> int:
        return np.maximum(np.random.normal(8, 2.8, size=size), 1).astype(np.int32)

    @staticmethod
    def _parse_datetime(year: int, month: int, day: int, flight_time: int):
        date_obj = date(year, month, day)
        time_obj = time(flight_time // 100, flight_time % 100)

        return datetime.combine(date_obj, time_obj)

    @staticmethod
    def _airlines_preprocessing(airlines_df: pd.DataFrame) -> pd.DataFrame:
        airlines_df['AIRLINE'] = airlines_df['AIRLINE'].fillna('Unkown')
        return airlines_df
    
    @staticmethod
    def _airports_preprocessing(airports_df: pd.DataFrame) -> pd.DataFrame:
        airports_df['TERMINALS'] = Reader._generate_terminals(airports_df.shape[0])
        return airports_df

    @staticmethod
    def _flights_preprocessing(
        flights_df: pd.DataFrame,
        airlines: Dict[str, Airline],
        airports: Dict[str, Airport],
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> pd.DataFrame:

        flights_df = flights_df[Reader.FLIGHTS_COLS].dropna()

        flights_df = flights_df[flights_df['ORIGIN_AIRPORT'].isin(airports)]
        flights_df = flights_df[flights_df['DESTINATION_AIRPORT'].isin(airports)]
        flights_df = flights_df[flights_df['AIRLINE'].isin(airlines)]

        flights_df['PRICE'] = Reader._generate_price(flights_df['DISTANCE'].to_numpy(np.int32))
        
        departure_datetimes = [
            Reader._parse_datetime(row.YEAR, row.MONTH, row.DAY, row.SCHEDULED_DEPARTURE)
            for row in flights_df.itertuples()
        ]
        arrival_datetimes = [
            departure + timedelta(minutes=scheduled_time)
            for departure, scheduled_time in zip(departure_datetimes, flights_df['SCHEDULED_TIME'])
        ]

        flights_df['DEPARTURE'] = departure_datetimes
        flights_df['ARRIVAL'] = arrival_datetimes

        if from_date is not None:
            flights_df = flights_df[flights_df['DEPARTURE'] >= from_date]

        if to_date is not None:
            flights_df = flights_df[flights_df['ARRIVAL'] <= to_date]

        return flights_df

    @staticmethod
    def read_flights(data_dir: str, from_date: datetime = None, to_date: datetime = None) -> Network:
        data_dir = Path(data_dir).resolve()

        # FIXME this should be infered by using max and min on the data
        if from_date is None:
            from_date = datetime(2015, 1, 1)
        if to_date is None:
            to_date = datetime(2015, 12, 31)

        if not data_dir.exists() or not data_dir.is_dir():
            raise ValueError('the given path does not exist or is not a directory')

        if any(not (data_dir / filename).exists() for filename in ['airlines.csv', 'airports.csv', 'flights.csv']):
            raise ValueError('either airlines.csv, airports.csv or flights.csv does not exist in the given data directory')

        airlines_df = pd.read_csv(data_dir / 'airlines.csv')
        airports_df = pd.read_csv(data_dir / 'airports.csv')
        flights_df = pd.read_csv(data_dir / 'flights.csv')

        airlines_df = Reader._airlines_preprocessing(airlines_df)
        airlines = {
            row.IATA_CODE: Airline(row.IATA_CODE, row.AIRLINE)
            for row in airlines_df.itertuples()
        }

        airports_df = Reader._airports_preprocessing(airports_df)
        airports = {
            row.IATA_CODE: Airport(row.IATA_CODE, row.AIRPORT, row.CITY, row.STATE, row.COUNTRY, row.LONGITUDE, row.LATITUDE, terminals=row.TERMINALS)
            for row in airports_df.itertuples()
        }

        flights_df = Reader._flights_preprocessing(flights_df, airlines, airports, from_date, to_date)
        flights = [
            Flight(
                origin=airports[row.ORIGIN_AIRPORT],
                destination=airports[row.DESTINATION_AIRPORT],
                airline=airlines[row.AIRLINE],
                departure=row.DEPARTURE,
                arrival=row.ARRIVAL,
                price=row.PRICE,
                miles=row.DISTANCE
            )
            for row in flights_df.itertuples()
        ]

        return Network(
            from_date,
            to_date,
            list(airlines.values()),
            list(airports.values()),
            flights
        )

    @staticmethod
    def read_network_pickled(pickle_path: str) -> Network:
        with open(pickle_path, 'rb') as f:
            network = pickle.load(f)

        assert type(network) == Network, 'pickled file does not contain a Network class or it is outdated'

        return network
