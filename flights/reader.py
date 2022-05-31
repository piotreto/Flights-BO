from datetime import datetime, date, time, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# from .data import Network, Airline, Airport, Flight
from data import Network, Airline, Airport, Flight


class Reader:
    FLIGHTS_COLS = ['YEAR', 'MONTH', 'DAY', 'AIRLINE', 'ORIGIN_AIRPORT', 'DESTINATION_AIRPORT', 'SCHEDULED_DEPARTURE', 'DISTANCE', 'SCHEDULED_TIME', 'SCHEDULED_ARRIVAL']

    # TODO I think we should create a much more complex distribution to generate price
    @staticmethod
    def _generate_price(dists: np.ndarray):
        return np.round(np.random.normal(0.2, 0.07, size=dists.shape[0]) * dists, 2)

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
    def _flights_preprocessing(flights_df: pd.DataFrame) -> pd.DataFrame:
        flights_df = flights_df[Reader.FLIGHTS_COLS].dropna()

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

        return flights_df

    @staticmethod
    def read_flights(data_dir: str):
        data_dir = Path(data_dir).resolve()

        if not data_dir.exists() or not data_dir.is_dir():
            raise ValueError('the given path does not exist or is not a directory')

        if any(not (data_dir / filename).exists() for filename in ['airlines.csv', 'airports.csv', 'flights.csv']):
            raise ValueError('either airlines.csv, airports.csv or flights.csv does not exist in the given data directory')

        airlines_df = pd.read_csv(data_dir / 'airlines.csv')
        airports_df = pd.read_csv(data_dir / 'airports.csv')
        flights_df = pd.read_csv(data_dir / 'flights.csv')

        airlines_df = Reader._airlines_preprocessing(airlines_df)
        airports_df = Reader._airports_preprocessing(airports_df)
        flights_df = Reader._flights_preprocessing(flights_df)

        airlines = {
            row.IATA_CODE: Airline(row.IATA_CODE, row.AIRLINE)
            for row in airlines_df.itertuples()
        }

        airports = {
            row.IATA_CODE: Airport(row.IATA_CODE, row.AIRPORT, row.CITY, row.STATE, row.COUNTRY, terminals=row.TERMINALS)
            for row in airports_df.itertuples()
        }

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
            list(airports.values()),
            flights.values(),
            list(airlines.values())
        )


if __name__ == '__main__':
    Reader.read_flights(Path('../../../data'))
