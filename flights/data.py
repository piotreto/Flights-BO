from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timedelta
from copy import copy


class Airport:
    def __init__(
        self, 
        codename: str,
        city: str,
        terminals: int = None,
        default_transfer_time: int = timedelta(minutes=15)
    ) -> None:

        self._codename = codename
        self._city = city

        # TODO eventually we can add proximate cities (the ones which are close enough to the airport to neglect the cost and time)

        self._terminals = terminals
        if terminals is not None:
            self._transfer_time = timedelta(minutes=15)  # TODO somehow calculate transfer time
        else:
            self._transfer_time = default_transfer_time

        self._in_flights: List[Flight] = []
        self._out_flights: List[Flight] = []


    @property
    def codename(self) -> str:
        return self._codename

    @property
    def city(self) -> str:
        return self._city

    @property
    def terminals(self) -> Optional[int]:
        return self._terminals

    @property
    def transfer_time(self) -> timedelta:
        return self._transfer_time

    @property
    def in_flights(self) -> List[Flight]:
        return copy(self._in_flights)

    @property
    def out_flights(self) -> List[Flight]:
        return copy(self._out_flights)

    def add_flight(self, flight: Flight):
        if self != flight.origin or self != flight.destination:
            raise ValueError('the airport you are adding flight to is neither its origin nor destination')
        
        if self == flight.origin:
            self._out_flights.append(flight)
        else:
            self._in_flights.append(flight)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Airport):
            return False
        return self.codename == __o.codename


class Flight:
    def __init__(
        self,
        origin: Airport,
        destination: Airport,
        departure: datetime,
        arrival: datetime,
        price: float,
        miles: int = None,
    ) -> None:
        
        self._origin = origin
        self._destination = destination

        if departure > arrival:
            raise ValueError('departure cannot happen after the arrival')

        self._departure = departure
        self._arrival = arrival
        
        self._price = price

        self._miles = miles

    @property
    def origin(self) -> Airport:
        return self._origin

    @property
    def destination(self) -> Airport:
        return self._destination

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
           and self.departure   == __o.departure \
           and self.arrival     == __o.arrival \
           and self.price       == __o.price


class Network:
    def __init__(self) -> None:
        pass
