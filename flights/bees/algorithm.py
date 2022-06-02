from __future__ import annotations

from operator import attrgetter
from typing import List, Iterator
from datetime import timedelta
from copy import copy

from tqdm import trange

from ..data import Network, Flight, Airport
from .configuration import BeeColonyConfiguration


class SolutionPath:
    def __init__(self, algorithm: BeeColonyAlgorithm, path: List[Flight]) -> None:
        self._path = copy(path)
        self._cost = algorithm.cost_function(path)

    def __len__(self) -> int:
        return len(self._path)
    
    def __getitem__(self, index: int) -> Flight:
        return self._path[index]
    
    def __iter__(self) -> Iterator:
        return iter(self._path)
        
    @property
    def path(self) -> List[Flight]:
        return self._path
    
    @property
    def cost(self) -> float:
        return self._cost

    
class Neighborhood:
    # TODO try out with frozen nodes, not flights, it should give us much better results
    def __init__(self, algorithm: BeeColonyAlgorithm, path: SolutionPath) -> None:
        self._algorithm = algorithm
        
        self._center_path: SolutionPath = path
        self._frozen_flights: List[Flight] = [path[0]]

        self._foragers = 0
        self._times_shrunk = 0
        self._abandoned = False

    @property
    def best_path(self) -> SolutionPath:
        return self._center_path
        
    @property
    def best_cost(self) -> float:
        return self._center_path.cost
        
    @property
    def times_shrunk(self) -> int:
        return self._times_shrunk

    @property
    def abandoned(self) -> bool:
        return self._abandoned
    
    def recruit(self, foragers_count: int):
        self._foragers = foragers_count

    def shrink(self) -> None:
        # if there is no more room to shrink (all the flights on the path are already frozen)
        if len(self._frozen_flights) == len(self._center_path):
            self._abandoned = True
            return

        newly_frozen_flight = self._center_path[len(self._frozen_flights)]
        self._frozen_flights.append(newly_frozen_flight)

        self._times_shrunk += 1
        
        if self._times_shrunk >= self._algorithm.configuration.max_shrinkages:
            self._abandoned = True
        
    def local_search(self) -> None:
        net = self._algorithm.network
        improved = False
        
        for _ in range(self._foragers):
            frozen_origin = self._frozen_flights[-1].destination
            
            path = self._frozen_flights + net.random_dfs_search(
                frozen_origin,
                self._center_path[-1].destination,
                self._frozen_flights[-1].arrival + frozen_origin.transfer_time
            )
            
            solution = SolutionPath(self._algorithm, path)
            
            if solution.cost < self.best_cost:
                self._center_path = solution
                improved = True
                
        if not improved:
            self.shrink()
            

class BeeColonyAlgorithm:
    def __init__(
        self,
        network: Network,
        configuration: BeeColonyConfiguration
    ) -> None:
        
        self._configuration = configuration
        self._network = network.filter_by_date(configuration.from_datetime, configuration.to_datetime)

    @property
    def network(self) -> Network:
        return self._network
    
    @property
    def configuration(self) -> BeeColonyConfiguration:
        return self._configuration
        
    def cost_function(self, path: List[Flight]) -> float:
        overall_time = (path[-1].arrival - path[0].departure) // timedelta(minutes=1)
        overall_price = sum(flight.price for flight in path)
        
        tp = self._configuration.time_priority
        # TODO how do we scale time and price
        return overall_price * (1 - tp) + (overall_time) * tp
        
    def global_search(self, source: Airport, target: Airport) -> Neighborhood:
        return Neighborhood(
            self,
            SolutionPath(self, self._network.random_dfs_search(source, target))
        )
        
    def run(self, source: Airport, target: Airport) -> List[Flight]:
        conf = self._configuration
        
        sites = [self.global_search(source, target) for _ in range(conf.scout_bees)]
        best_path = sites[0].best_path
        
        for _ in trange(conf.iterations):
            sorted_sites = sorted(sites, key=attrgetter('best_cost'))[:conf.best_sites]
            
            if sorted_sites[0].best_cost < best_path.cost:
                best_path = sorted_sites[0].best_path
            
            elite_sites = sorted_sites[:conf.elite_sites]
            rest_sites = sorted_sites[conf.elite_sites:]

            for site in elite_sites:
                site.recruit(conf.elite_sites_bees)
            for site in rest_sites:
                site.recruit(conf.rest_sites_bees)
                
            for site in sorted_sites:
                site.local_search()
                
            # constructing list of sites for the next iteration
            left_sites = [
                site for site in sorted_sites if not site.abandoned
            ]
            
            new_sites = [
                self.global_search(source, target)
                for _ in range(conf.scout_bees - len(left_sites))
            ]
            
            sites = left_sites + new_sites
            
        return best_path.path
